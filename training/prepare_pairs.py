"""Utilities for creating a labelled training set for the ranker.

The ranker in :mod:`training.train_ranker` expects a table with the
following columns:

``query_full_name, query_dob, query_phone, query_email, query_gov_id,
query_addr, query_city, query_state, query_pc, query_ctry,
cand_customer_id, label``

``prepare_pairs.py`` samples rows from the ``USERS.CUSTOMERS`` table and
emits pairs of a *query* (the fields above prefixed with ``query_``) and a
candidate ``customer_id``.  ``label`` is ``1`` when the candidate is a true
duplicate of the query row and ``0`` for hard negatives.

The script writes the result to ``labeled_pairs.csv`` by default but will
also emit Parquet when the output path ends with ``.parquet``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import os
import random
import json
from concurrent.futures import ThreadPoolExecutor

import math
import numpy as np
import pandas as pd
from tqdm import tqdm

# Allow running this script directly without installing the package by adding the
# repository root to ``sys.path`` when ``app`` cannot be imported normally.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.db import get_conn, topk_by_vector
from app.normalization import canonical_identity_text
from app.embeddings import embed_identity, embed_identities
import tempfile


def _row_to_query(row: Mapping[str, object]) -> dict[str, object]:
    """Return a dictionary of query fields from a customer row.

    ``row`` may be a :class:`pandas.Series` or a plain ``dict`` which allows
    callers to pre-convert the dataframe to a list of dictionaries for faster
    iteration.
    """

    dob = row.get("dob")
    if pd.notna(dob):
        dob = str(pd.to_datetime(dob).date())

    return {
        "query_full_name": row.get("full_name"),
        "query_dob": dob,
        "query_phone":
            str(row.get("phone_e164")) if row.get("phone_e164") is not None else None,
        "query_email": row.get("email_norm"),
        "query_gov_id": row.get("gov_id_norm"),
        "query_addr": row.get("addr_line"),
        "query_city": row.get("city"),
        "query_state": row.get("state"),
        "query_pc":
            str(row.get("postal_code")) if row.get("postal_code") is not None else None,
        "query_ctry": row.get("country"),
    }


def _query_vector(row: Mapping[str, object]) -> Sequence[float]:
    """Return the embedding for ``row``.

    Existing tests patch this function so we retain it for compatibility.  When
    ``identity_vec`` is present it is returned directly; otherwise the canonical
    identity text is embedded on demand.
    """

    if "identity_vec" in row:
        return row["identity_vec"]
    ident = canonical_identity_text(
        row.get("full_name"),
        row.get("dob"),
        row.get("phone_e164"),
        row.get("email_norm"),
        row.get("gov_id_norm"),
        row.get("addr_line"),
        row.get("city"),
        row.get("state"),
        row.get("postal_code"),
        row.get("country"),
    )
    return embed_identity(ident)


def _hard_negative(
    conn,
    qvec: Sequence[float],
    exclude_ids: Iterable[int],
    k: int = 20,
    *,
    all_vecs: np.ndarray | None = None,
    all_ids: np.ndarray | None = None,
) -> int | None:
    """Return the ``customer_id`` of a near neighbour not in ``exclude_ids``.

    When ``all_vecs``/``all_ids`` are provided the search is performed in-memory,
    allowing the utility to run without a live database.  Otherwise the vector
    index in Oracle is queried.
    """

    if all_vecs is not None and all_ids is not None:
        q = np.asarray(qvec, dtype=float)
        dists = np.linalg.norm(all_vecs - q, axis=1)
        order = np.argsort(dists)
        for idx in order:
            cid = int(all_ids[idx])
            if cid not in exclude_ids:
                return cid
        return None

    if conn is None:
        with get_conn() as conn2:
            rows = topk_by_vector(conn2, qvec, k)
    else:
        rows = topk_by_vector(conn, qvec, k)
    for row in rows:
        cid = int(row[0])
        if cid not in exclude_ids:
            return cid
    return None


def generate_pairs_df(
    *,
    input_path: str | None = None,
    max_pos_per_query: int | None = 5,
    workers: int | None = None,
    max_pairs: int | None = None,
) -> pd.DataFrame:
    """Return a dataframe of query/candidate pairs for training.

    This convenience wrapper runs :func:`main` using a temporary file and
    returns the resulting data as a :class:`pandas.DataFrame`.

    Parameters are identical to :func:`main` except ``output_path`` which is
    handled internally.
    """

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        main(
            tmp_path,
            input_path=input_path,
            max_pos_per_query=max_pos_per_query,
            workers=workers,
            max_pairs=max_pairs,
        )
        return pd.read_csv(tmp_path, dtype=str)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def main(
    output_path: str = "labeled_pairs.csv",
    *,
    input_path: str | None = None,
    chunk_size: int = 10_000,
    max_pos_per_query: int | None = 5,
    workers: int | None = None,
    max_pairs: int | None = None,
) -> None:
    """Sample query/candidate pairs from the customer table or a flat file.

    The function identifies duplicate clusters using ``identity_text``.  For
    each row in a cluster it emits up to ``max_pos_per_query`` positive examples
    (other rows in the cluster) and a hard negative mined from the vector index
    or an in-memory search when ``input_path`` is provided.

    Parameters
    ----------
    output_path:
        Destination file to write.  ``.csv`` and ``.parquet`` extensions are
        recognised.
    input_path:
        Optional path to a CSV/Parquet file containing customer records.  When
        supplied the database is not queried and all processing happens locally.
    chunk_size:
        Number of pairs to accumulate in memory before flushing to ``output``.
        Chunked writing avoids holding the entire training set in memory which
        previously resulted in :class:`MemoryError` for large databases.
    max_pos_per_query:
        Maximum number of positive pairs to emit for each query.  ``None``
        generates all possible positives which can grow quadratically for large
        clusters.
    workers:
        Number of threads for hard-negative mining.  Defaults to the number of
        CPU cores.
    max_pairs:
        Optional maximum number of query/candidate pairs to generate.  When
        provided the function stops once this many pairs have been emitted.
    """

    if workers is None:
        workers = os.cpu_count() or 1

    if input_path:
        if input_path.lower().endswith((".csv", ".tsv")):
            df = pd.read_csv(input_path)
        else:
            df = pd.read_parquet(input_path)
        conn = None
    else:
        conn = get_conn()
        sql = """
            SELECT customer_id, full_name, dob, phone_e164, email_norm,
                   gov_id_norm, addr_line, city, state, postal_code,
                   country, identity_text
            FROM USERS.CUSTOMERS
        """
        with tqdm(total=1, desc="Fetching customers") as pbar:
            if hasattr(conn, "cursor"):
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall()
                    col_names = [c[0] for c in cur.description]
                df = pd.DataFrame(rows, columns=col_names)
            else:  # pragma: no cover - exercised only in tests with DummyConn
                df = pd.read_sql(sql, conn)
            pbar.update()
        try:
            df = df.map(lambda x: x.read() if hasattr(x, "read") else x)
        except AttributeError:  # pragma: no cover - pandas < 2.1
            df = df.applymap(lambda x: x.read() if hasattr(x, "read") else x)

        df.columns = df.columns.str.lower()
        if "customer_id" not in df.columns:
            raise KeyError("customer_id column is missing from USERS.CUSTOMERS")
        if "identity_text" not in df.columns:
            def _ident_text(row: pd.Series) -> str:
                dob = row.get("dob")
                if pd.notna(dob):
                    dob = str(pd.to_datetime(dob).date())
                else:
                    dob = None
                return canonical_identity_text(
                    row.get("full_name"),
                    dob,
                    row.get("phone_e164"),
                    row.get("email_norm"),
                    row.get("gov_id_norm"),
                    row.get("addr_line"),
                    row.get("city"),
                    row.get("state"),
                    row.get("postal_code"),
                    row.get("country"),
                )

            df["identity_text"] = df.apply(_ident_text, axis=1)

    df.columns = df.columns.str.lower()

    if "identity_vec" in df.columns:
        df["identity_vec"] = df["identity_vec"].apply(
            lambda v: json.loads(v) if isinstance(v, str) else v
        )
    else:
        texts = df["identity_text"].tolist()
        chunk_size = 64
        total_chunks = math.ceil(len(texts) / chunk_size) if texts else 0

        def _chunks(seq: list[str], size: int):
            for i in range(0, len(seq), size):
                yield seq[i : i + size]

        vecs: list[list[float]] = []
        for chunk in tqdm(
            _chunks(texts, chunk_size),
            total=total_chunks,
            desc="Embedding customers",
        ):
            vecs.extend(embed_identities(chunk).tolist())
        df["identity_vec"] = vecs

    all_vecs = np.asarray(df["identity_vec"].tolist(), dtype=float)
    all_ids = df["customer_id"].to_numpy()

    pairs: list[dict[str, object]] = []
    header_written = False
    total_pairs = 0

    # ``ParquetWriter`` is used only when writing Parquet so import lazily
    pq_writer = None
    if output_path.lower().endswith((".parquet", ".pq")):
        import pyarrow as pa
        import pyarrow.parquet as pq

        pq_writer = None

        def _write_chunk(chunk: list[dict[str, object]]) -> None:
            nonlocal pq_writer
            if not chunk:
                return
            table = pa.Table.from_pylist(chunk)
            if pq_writer is None:
                pq_writer = pq.ParquetWriter(output_path, table.schema)
            pq_writer.write_table(table)
    else:
        def _write_chunk(chunk: list[dict[str, object]]) -> None:
            nonlocal header_written
            if not chunk:
                return
            df_chunk = pd.DataFrame(chunk)
            mode = "w" if not header_written else "a"
            df_chunk.to_csv(
                output_path,
                index=False,
                header=not header_written,
                mode=mode,
            )
            header_written = True

    with tqdm(total=max_pairs if max_pairs is not None else len(df), desc="Generating pairs") as pbar:
        for _, group in df.groupby("identity_text"):
            if max_pairs is not None and total_pairs >= max_pairs:
                break
            if len(group) <= 1:
                continue

            records = group.to_dict("records")
            ids = [int(r["customer_id"]) for r in records]
            id_set = set(ids)
            queries = [_row_to_query(r) for r in records]

            qvecs = [r["identity_vec"] for r in records]

            def _hn(v):
                try:
                    return _hard_negative(
                        conn, v, id_set, all_vecs=all_vecs, all_ids=all_ids
                    )
                except TypeError:
                    # Some test stubs don't accept the extra parameters.
                    return _hard_negative(conn, v, id_set)

            with ThreadPoolExecutor(max_workers=workers) as ex:
                neg_ids = list(ex.map(_hn, qvecs))

            for q_fields, cid, neg_id in zip(queries, ids, neg_ids):
                if max_pairs is not None and total_pairs >= max_pairs:
                    break
                positives = [cand_id for cand_id in ids if cand_id != cid]
                if (
                    max_pos_per_query is not None
                    and len(positives) > max_pos_per_query
                ):
                    positives = random.sample(positives, max_pos_per_query)
                for cand_id in positives:
                    if max_pairs is not None and total_pairs >= max_pairs:
                        break
                    pairs.append(
                        q_fields
                        | {
                            "cand_customer_id": cand_id,
                            "label": 1,
                        }
                    )
                    total_pairs += 1
                    pbar.update(1)
                    if len(pairs) >= chunk_size:
                        _write_chunk(pairs)
                        pairs = []
                if max_pairs is not None and total_pairs >= max_pairs:
                    break
                if neg_id is not None and (
                    max_pairs is None or total_pairs < max_pairs
                ):
                    pairs.append(
                        q_fields | {"cand_customer_id": neg_id, "label": 0}
                    )
                    total_pairs += 1
                    pbar.update(1)
                    if len(pairs) >= chunk_size:
                        _write_chunk(pairs)
                        pairs = []

    # flush any remaining pairs
    _write_chunk(pairs)
    if pq_writer is not None:
        pq_writer.close()
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sample query/candidate pairs for ranker training"
    )
    parser.add_argument(
        "--output",
        default="labeled_pairs.csv",
        help="Path to CSV or Parquet file to write",
    )
    parser.add_argument(
        "--input",
        help="Optional CSV/Parquet file with customer records (bypasses DB)",
    )
    parser.add_argument(
        "--max-pos-per-query",
        type=int,
        default=5,
        help="Maximum number of positive pairs to emit per query (default: 5)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of threads for hard-negative mining",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        help="Maximum number of pairs to generate",
    )
    args = parser.parse_args()
    main(
        args.output,
        input_path=args.input,
        max_pos_per_query=args.max_pos_per_query,
        workers=args.workers,
        max_pairs=args.max_pairs,
    )

