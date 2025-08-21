import time
import uuid
import numpy as np
from sklearn.linear_model import LogisticRegression
from app.features import feature_row
from app.db import get_conn
from app.model_store import save_model
from app.normalization import canonical_identity_text, norm_postal_code
from app.embeddings import embed_identity
from app.deduper import candidate_dict
from app.db import to_vec_array
from training.data_loader import load_dataframe

def fetch_candidate_row(conn, customer_id, qvec):
    # Single candidate's vdist against qvec
    cur = conn.cursor()
    cur.execute("INSERT INTO query_identity(qvec) VALUES (:1)", [to_vec_array(qvec)])
    cur.execute("SELECT qid FROM query_identity ORDER BY qid DESC FETCH FIRST 1 ROWS ONLY")
    qid = cur.fetchone()[0]

    sql = """
    WITH q AS (SELECT qvec FROM query_identity WHERE qid = :qid)
    SELECT c.customer_id, VECTOR_DISTANCE(c.identity_vec, q.qvec) AS vdist,
           c.full_name, c.dob, c.phone_e164, c.email_norm, c.gov_id_norm,
           c.addr_line, c.city, c.state, c.postal_code
    FROM USERS.CUSTOMERS c, q
    WHERE c.customer_id = :cid
    """
    cur.execute(sql, dict(qid=qid, cid=customer_id))
    row = cur.fetchone()
    cur.execute("DELETE FROM query_identity WHERE qid = :qid", dict(qid=qid))
    conn.commit()
    return candidate_dict(row)

def main(pairs_path: str = "labeled_pairs.csv"):
    start = time.time()
    df = load_dataframe(pairs_path)
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
                postal_code=norm_postal_code(r.get("query_pc")),
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
    X_arr = np.asarray(X)
    y_arr = np.asarray(y)
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_arr, y_arr)
    save_model(model)
    duration = time.time() - start
    accuracy = float(model.score(X_arr, y_arr))
    info = {
        "success": True,
        "message": "Model trained successfully",
        "training_id": uuid.uuid4().hex[:8],
        "details": {
            "pairs_processed": len(df),
            "accuracy": accuracy,
            "training_time": duration,
        },
    }
    print("Saved model.bin")
    return info

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train the duplicate detection ranker")
    parser.add_argument(
        "pairs_path",
        nargs="?",
        default="labeled_pairs.csv",
        help="Path to CSV/Parquet file or Hugging Face dataset directory",
    )
    args = parser.parse_args()
    main(args.pairs_path)
