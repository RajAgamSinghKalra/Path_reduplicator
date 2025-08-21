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
from typing import Iterable, Sequence

import pandas as pd
from tqdm.auto import tqdm

# Allow running this script directly without installing the package by adding the
# repository root to ``sys.path`` when ``app`` cannot be imported normally.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.db import get_conn, topk_by_vector
from app.normalization import canonical_identity_text
from app.embeddings import embed_identity


def _row_to_query(row: pd.Series) -> dict[str, object]:
    """Return a dictionary of query fields from a customer row."""

    dob = row.get("dob")
    if pd.notna(dob):
        dob = str(pd.to_datetime(dob).date())

    return {
        "query_full_name": row.get("full_name"),
        "query_dob": dob,
        "query_phone": row.get("phone_e164"),
        "query_email": row.get("email_norm"),
        "query_gov_id": row.get("gov_id_norm"),
        "query_addr": row.get("addr_line"),
        "query_city": row.get("city"),
        "query_state": row.get("state"),
        "query_pc": row.get("postal_code"),
        "query_ctry": row.get("country"),
    }


def _query_vector(row: pd.Series) -> Sequence[float]:
    """Compute the embedding for ``row`` used to mine hard negatives."""

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
    conn, qvec: Sequence[float], exclude_ids: Iterable[int], k: int = 20
) -> int | None:
    """Return the ``customer_id`` of a near neighbour not in ``exclude_ids``."""

    rows = topk_by_vector(conn, qvec, k)
    for row in rows:
        cid = int(row[0])
        if cid not in exclude_ids:
            return cid
    return None


def main(output_path: str = "labeled_pairs.csv", *, chunk_size: int = 10_000) -> None:
    """Sample query/candidate pairs from the customer table.

    The function identifies duplicate clusters using ``identity_text``.  For
    each row in a cluster it emits one or more positive examples (other rows
    in the cluster) and a hard negative mined from the vector index.

    Parameters
    ----------
    output_path:
        Destination file to write.  ``.csv`` and ``.parquet`` extensions are
        recognised.
    chunk_size:
        Number of pairs to accumulate in memory before flushing to ``output``.
        Chunked writing avoids holding the entire training set in memory which
        previously resulted in :class:`MemoryError` for large databases.
    """

    with get_conn() as conn:
        sql = """
            SELECT customer_id, full_name, dob, phone_e164, email_norm,
                   gov_id_norm, addr_line, city, state, postal_code,
                   country, identity_text
            FROM USERS.CUSTOMERS
        """
        df = pd.read_sql(sql, conn)
        # Oracle returns LOB objects for ``CLOB`` columns which are not directly
        # comparable and cause ``groupby`` to fail with ``TypeError: '<'
        # not supported between instances of 'LOB' and 'LOB'``.  Convert any
        # value with a ``read`` attribute (as exposed by ``oracledb.LOB``) to a
        # plain string so pandas can safely factorize and group on them.  ``DataFrame.map``
        # is preferred but fall back to ``applymap`` for older pandas versions.
        try:
            df = df.map(lambda x: x.read() if hasattr(x, "read") else x)
        except AttributeError:  # pragma: no cover - pandas < 2.1
            df = df.applymap(lambda x: x.read() if hasattr(x, "read") else x)

        # Oracle returns column names in uppercase by default which causes key
        # lookups like ``row["customer_id"]`` to fail.  Normalize the columns to
        # lowercase so the rest of the code can consistently reference them.
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

        pairs: list[dict[str, object]] = []
        header_written = False

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

        n_clusters = df["identity_text"].nunique()
        for _, group in tqdm(
            df.groupby("identity_text"), total=n_clusters, desc="Generating pairs"
        ):
            if len(group) <= 1:
                continue

            ids = set(int(x) for x in group["customer_id"].tolist())
            for _, q in group.iterrows():
                q_fields = _row_to_query(q)

                # Positive pairs for other members of the cluster
                others = group[group["customer_id"] != q["customer_id"]]
                for _, cand in others.iterrows():
                    pairs.append(
                        q_fields
                        | {
                            "cand_customer_id": int(cand["customer_id"]),
                            "label": 1,
                        }
                    )
                    if len(pairs) >= chunk_size:
                        _write_chunk(pairs)
                        pairs = []

                # Hard negative
                qvec = _query_vector(q)
                neg_id = _hard_negative(conn, qvec, ids)
                if neg_id is not None:
                    pairs.append(q_fields | {"cand_customer_id": neg_id, "label": 0})
                    if len(pairs) >= chunk_size:
                        _write_chunk(pairs)
                        pairs = []

        # flush any remaining pairs
        _write_chunk(pairs)
        if pq_writer is not None:
            pq_writer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sample query/candidate pairs for ranker training"
    )
    parser.add_argument(
        "--output",
        default="labeled_pairs.csv",
        help="Path to CSV or Parquet file to write",
    )
    args = parser.parse_args()
    main(args.output)

