from fastapi import FastAPI
from pydantic import BaseModel
from app.deduper import check_duplicate
from app.normalization import canonical_identity_text
from app.embeddings import embed_identity
from app.db import get_conn
from app.config import Config

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
    ident = canonical_identity_text(
        q.get("full_name"), q.get("dob"), q.get("phone"), q.get("email"), q.get("gov_id"),
        q.get("addr_line"), q.get("city"), q.get("state"), q.get("postal_code"), q.get("country")
    )
    vec = embed_identity(ident)

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
        # Normalize fields similarly to check_duplicate (kept simple here)
        bind = {
            "full_name": q.get("full_name"),
            "dob": q.get("dob"),
            "phone_e164": q.get("phone"),
            "email_norm": (q.get("email") or "").lower(),
            "gov_id_norm": (q.get("gov_id") or "").upper(),
            "addr_line": q.get("addr_line"),
            "city": q.get("city"),
            "state": q.get("state"),
            "postal_code": q.get("postal_code"),
            "country": q.get("country") or "IN",
            "identity_text": ident,
            "identity_vec": vec.tolist(),  # oracledb will still want array('f', ...); fallback below
        }
        # Safer bind for vector:
        import array
        bind["identity_vec"] = array.array('f', vec)

        cur.execute(sql, bind)
        conn.commit()
    return {"status": "ok"}
