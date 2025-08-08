from .config import Config
from .normalization import canonical_identity_text, norm_name, norm_email, norm_phone_e164, norm_govid
from .embeddings import embed_identity
from .db import get_conn, topk_by_vector
from .features import feature_row
from .model_store import load_model, predict_proba

def to_query_obj(payload):
    return {
        "full_name": payload.get("full_name"),
        "dob": payload.get("dob"),  # ISO yyyy-mm-dd (string)
        "phone_e164": norm_phone_e164(payload.get("phone")),
        "email_norm": norm_email(payload.get("email")),
        "gov_id_norm": norm_govid(payload.get("gov_id")),
        "addr_line": payload.get("addr_line"),
        "city": payload.get("city"),
        "state": payload.get("state"),
        "postal_code": payload.get("postal_code"),
        "country": payload.get("country", "IN"),
    }

def candidate_dict(row):
    return {
        "customer_id": row[0],
        "vdist": float(row[1]),
        "full_name": row[2],
        "dob": row[3].isoformat() if row[3] else None,
        "phone_e164": row[4],
        "email_norm": row[5],
        "gov_id_norm": row[6],
        "city": row[7],
        "state": row[8],
    }

def check_duplicate(payload):
    q = to_query_obj(payload)
    identity_text = canonical_identity_text(
        q["full_name"], q["dob"], q["phone_e164"], q["email_norm"], q["gov_id_norm"],
        q["addr_line"], q["city"], q["state"], q["postal_code"], q["country"]
    )
    qvec = embed_identity(identity_text)

    with get_conn() as conn:
        rows = topk_by_vector(conn, qvec, Config.TOPK)

    candidates = [candidate_dict(r) for r in rows]

    # Features & scoring
    X = [feature_row(q, c, c["vdist"]) for c in candidates]
    model = load_model()
    if len(X) == 0:
        return { "is_duplicate": False, "best_match": None, "score": 0.0, "candidates": [] }

    probs = predict_proba(model, X)
    for c, p in zip(candidates, probs):
        c["score"] = float(p)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]
    return {
        "is_duplicate": best["score"] >= Config.THRESHOLD,
        "best_match": best,
        "score": best["score"],
        "candidates": candidates[:10]  # top 10 with evidence
    }
