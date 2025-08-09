from fastapi import FastAPI
from pydantic import BaseModel
from app.deduper import check_duplicate
from app.normalization import (
    canonical_identity_text,
    norm_phone_e164,
    norm_email,
    norm_govid,
    norm_postal_code,
)
from app.embeddings import embed_identity
from app.db import get_conn, to_vec_array

app = FastAPI(title="Reduplicator (Oracle 23ai)")

class Customer(BaseModel):
    full_name: str
    dob: str | None = None
    phone: str | None = None
    email: str | None = None
    gov_id: str | None = None
    addr_line: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = "IN"

@app.post("/dedupe/check")
def dedupe_check(cust: Customer):
    return check_duplicate(cust.dict())

@app.post("/customers")
def create_customer(cust: Customer):
    q = cust.dict()
    normed = {
        "full_name": q.get("full_name"),
        "dob": q.get("dob"),
        "phone_e164": norm_phone_e164(q.get("phone")),
        "email_norm": norm_email(q.get("email")),
        "gov_id_norm": norm_govid(q.get("gov_id")),
        "addr_line": q.get("addr_line"),
        "city": q.get("city"),
        "state": q.get("state"),
        "postal_code": norm_postal_code(q.get("postal_code")),
        "country": q.get("country") or "IN",
    }
    ident = canonical_identity_text(
        normed["full_name"], normed["dob"], normed["phone_e164"], normed["email_norm"], normed["gov_id_norm"],
        normed["addr_line"], normed["city"], normed["state"], normed["postal_code"], normed["country"]
    )
    vec = embed_identity(ident)

    with get_conn() as conn, conn.cursor() as cur:
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
        bind = {
            "full_name": normed["full_name"],
            "dob": normed["dob"],
            "phone_e164": normed["phone_e164"],
            "email_norm": normed["email_norm"],
            "gov_id_norm": normed["gov_id_norm"],
            "addr_line": normed["addr_line"],
            "city": normed["city"],
            "state": normed["state"],
            "postal_code": normed["postal_code"],
            "country": normed["country"],
            "identity_text": ident,
            "identity_vec": to_vec_array(vec),
        }

        cur.execute(sql, bind)
        conn.commit()
    return {"status": "ok"}
