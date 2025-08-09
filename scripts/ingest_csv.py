import csv
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


def ingest_csv(path: str):
    with open(path, newline='', encoding='utf-8') as f, get_conn() as conn:
        reader = csv.DictReader(f)
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
        for row in reader:
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
    parser = argparse.ArgumentParser(description="Ingest customers from CSV")
    parser.add_argument("csv_path", help="Path to CSV file")
    args = parser.parse_args()
    ingest_csv(args.csv_path)
