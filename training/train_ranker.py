import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from app.features import feature_row
from app.db import get_conn
from app.config import Config
from app.model_store import save_model
from app.normalization import canonical_identity_text
from app.embeddings import embed_identity
from app.deduper import candidate_dict
from app.db import to_vec_array

def fetch_candidate_row(conn, customer_id, qvec):
    # Single candidate's vdist against qvec
    cur = conn.cursor()
    cur.execute("INSERT INTO query_identity(qvec) VALUES (:1)", [to_vec_array(qvec)])
    cur.execute("SELECT qid FROM query_identity ORDER BY qid DESC FETCH FIRST 1 ROWS ONLY")
    qid = cur.fetchone()[0]

    sql = """
    WITH q AS (SELECT qvec FROM query_identity WHERE qid = :qid)
    SELECT c.customer_id, VECTOR_DISTANCE(c.identity_vec, q.qvec) AS vdist,
           c.full_name, c.dob, c.phone_e164, c.email_norm, c.gov_id_norm, c.city, c.state
    FROM customers c, q
    WHERE c.customer_id = :cid
    """
    cur.execute(sql, dict(qid=qid, cid=customer_id))
    row = cur.fetchone()
    cur.execute("DELETE FROM query_identity WHERE qid = :qid", dict(qid=qid))
    conn.commit()
    return candidate_dict(row)

def main(pairs_csv="labeled_pairs.csv"):
    df = pd.read_csv(pairs_csv)
    X, y = [], []
    with get_conn() as conn:
        for _, r in df.iterrows():
            q = dict(
                full_name=r["query_full_name"],
                dob=r.get("query_dob"),
                phone_e164=r.get("query_phone"),
                email_norm=r.get("query_email"),
                gov_id_norm=r.get("query_gov_id"),
                addr_line=r.get("query_addr"),
                city=r.get("query_city"),
                state=r.get("query_state"),
                postal_code=r.get("query_pc"),
                country=r.get("query_ctry"),
            )
            ident = canonical_identity_text(
                q["full_name"], q["dob"], q["phone_e164"], q["email_norm"], q["gov_id_norm"],
                q["addr_line"], q["city"], q["state"], q["postal_code"], q["country"]
            )
            qvec = embed_identity(ident)
            cand = fetch_candidate_row(conn, int(r["cand_customer_id"]), qvec)
            X.append(feature_row(q, cand, cand["vdist"]))
            y.append(int(r["label"]))
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(np.asarray(X), np.asarray(y))
    save_model(model)
    print("Saved model.bin")

if __name__ == "__main__":
    main()
