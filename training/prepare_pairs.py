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
from typing import Iterable, Sequence

import pandas as pd

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


def main(output_path: str = "labeled_pairs.csv") -> None:
    """Sample query/candidate pairs from the customer table.

    The function identifies duplicate clusters using ``identity_text``.  For
    each row in a cluster it emits one or more positive examples (other rows
    in the cluster) and a hard negative mined from the vector index.
    """

    with get_conn() as conn:
        sql = """
            SELECT customer_id, full_name, dob, phone_e164, email_norm,
                   gov_id_norm, addr_line, city, state, postal_code,
                   country, identity_text
            FROM USERS.CUSTOMERS
        """
        df = pd.read_sql(sql, conn)

        pairs: list[dict[str, object]] = []
        for _, group in df.groupby("identity_text"):
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

                # Hard negative
                qvec = _query_vector(q)
                neg_id = _hard_negative(conn, qvec, ids)
                if neg_id is not None:
                    pairs.append(q_fields | {"cand_customer_id": neg_id, "label": 0})

        out_df = pd.DataFrame(pairs)
        if output_path.lower().endswith(('.parquet', '.pq')):
            out_df.to_parquet(output_path, index=False)
        else:
            out_df.to_csv(output_path, index=False)


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

