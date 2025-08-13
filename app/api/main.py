from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, ConfigDict
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

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
from app.config import Config
from training.train_ranker import main as train_ranker

app = FastAPI(title="Reduplicator (Oracle 23ai)")

class Customer(BaseModel):
    full_name: str
    dob: str | None = Field(None, alias="date_of_birth")
    phone: str | None = None
    email: str | None = None
    gov_id: str | None = Field(None, alias="government_id")
    addr_line: str | None = Field(None, alias="address_line")
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = "IN"

    model_config = ConfigDict(populate_by_name=True)

class TrainRequest(BaseModel):
    data_path: str = Field("labeled_pairs.csv", alias="csv_path")

    model_config = ConfigDict(populate_by_name=True)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    try:
        with get_conn():
            pass
    except Exception as exc:
        raise HTTPException(status_code=503, detail="db unavailable") from exc
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
def stats():
    """Return basic applicant metrics derived from the database."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM customers")
        total = cur.fetchone()[0] or 0

        cur.execute(
            "SELECT COUNT(*) FROM customers WHERE TRUNC(created_at) = TRUNC(SYSDATE)"
        )
        today = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT gov_id_norm, COUNT(*) c
                FROM customers
                WHERE gov_id_norm IS NOT NULL
                GROUP BY gov_id_norm
                HAVING COUNT(*) > 1
            )
            """
        )
        dup = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT gov_id_norm, COUNT(*) c
                FROM customers
                WHERE gov_id_norm IS NOT NULL
                GROUP BY gov_id_norm
                HAVING COUNT(*) >= 5
            )
            """
        )
        high_risk = cur.fetchone()[0] or 0

    rate = round((today / total) * 100, 1) if total else 0.0
    return {
        "total_applicants": total,
        "today_applicants": today,
        "duplicate_alerts": dup,
        "high_risk_duplicates": high_risk,
        "processing_rate": rate,
    }

@app.post("/train")
def train(req: TrainRequest):
    train_ranker(req.data_path)
    return {"status": "trained"}

@app.post("/dedupe/check")
def dedupe_check(cust: Customer):
    result = check_duplicate(cust.model_dump())

    def rename(c):
        return {
            "customer_id": c.get("customer_id"),
            "name": c.get("full_name"),
            "date_of_birth": c.get("dob"),
            "phone": c.get("phone_e164"),
            "email": c.get("email_norm"),
            "government_id": c.get("gov_id_norm"),
            "address_line": c.get("addr_line"),
            "city": c.get("city"),
            "state": c.get("state"),
            "postal_code": c.get("postal_code"),
            "score": c.get("score"),
            "vector_distance": c.get("vdist"),
        }

    best = result.get("best_match")
    candidates = [rename(c) for c in result.get("candidates", [])]
    return {
        "is_duplicate": result.get("is_duplicate", False),
        "score": result.get("score", 0.0),
        "threshold": Config.THRESHOLD,
        "best_match": rename(best) if best else None,
        "candidates": candidates,
    }

@app.post("/customers")
def create_customer(cust: Customer):
    q = cust.model_dump()
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
