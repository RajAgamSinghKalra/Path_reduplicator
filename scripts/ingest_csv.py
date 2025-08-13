import argparse

from app.normalization import (
    canonical_identity_text,
    norm_phone_e164,
    norm_email,
    norm_govid,
    norm_postal_code,
)
from app.embeddings import embed_identity
from app.db import get_conn, to_vec_array
from training.data_loader import load_dataframe


def ingest_data(path: str):
    df = load_dataframe(path)
    with get_conn() as conn:
        cur = conn.cursor()
        sql = """
        INSERT INTO customers(
            full_name, dob, phone_e164, email_norm, gov_id_norm,
            addr_line, city, state, postal_code, country, identity_text, identity_vec
        ) VALUES (
            :full_name,
            TO_DATE(:dob, 'YYYY-MM-DD'),
            :phone_e164, :email_norm, :gov_id_norm,
            :addr_line, :city, :state, :postal_code, :country,
            :identity_text, :identity_vec
        )
        """
        for _, row in df.iterrows():
            normed = {
                "full_name": row.get("full_name"),
                "dob": row.get("dob"),
                "phone_e164": norm_phone_e164(row.get("phone")),
                "email_norm": norm_email(row.get("email")),
                "gov_id_norm": norm_govid(row.get("gov_id")),
                "addr_line": row.get("addr_line"),
                "city": row.get("city"),
                "state": row.get("state"),
                "postal_code": norm_postal_code(row.get("postal_code")),
                "country": row.get("country") or "IN",
            }
            ident = canonical_identity_text(
                normed["full_name"], normed["dob"], normed["phone_e164"], normed["email_norm"], normed["gov_id_norm"],
                normed["addr_line"], normed["city"], normed["state"], normed["postal_code"], normed["country"]
            )
            vec = embed_identity(ident)
            bind = normed | {"identity_text": ident, "identity_vec": to_vec_array(vec)}
            cur.execute(sql, bind)
        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest customers from a dataset file")
    parser.add_argument("data_path", help="Path to CSV/Parquet file or dataset directory")
    args = parser.parse_args()
    ingest_data(args.data_path)
