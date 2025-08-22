import time
import uuid
import os
import sys
from pathlib import Path

import math
import numpy as np
from sklearn.linear_model import LogisticRegression
from joblib import Parallel, delayed
import joblib
from tqdm.auto import tqdm
from contextlib import contextmanager


@contextmanager
def tqdm_joblib(tqdm_object):
    """Context manager to patch joblib to report into ``tqdm`` progress bar."""

    class TqdmBatchCallback(joblib.parallel.BatchCompletionCallBack):
        def __call__(self, *args, **kwargs):  # pragma: no cover - passthrough
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_cb = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_cb
        tqdm_object.close()

# Ensure the repository root is on ``sys.path`` so that the ``app`` package can
# be imported when running this script directly (``python training/train_ranker.py``).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.features import feature_row
from app.db import get_conn
from app.model_store import save_model
from app.normalization import canonical_identity_text, norm_postal_code
from app import embeddings
from app.deduper import candidate_dict
from app.db import to_vec_array, ensure_query_identity_table
from training.data_loader import load_dataframe
from training.prepare_pairs import generate_pairs_df

# Prefer the dGPU (6550m) via DirectML when available.
try:  # pragma: no cover - directml typically unavailable in CI
    import torch_directml

    _device = None
    if hasattr(torch_directml, "device_count"):
        for i in range(torch_directml.device_count()):
            name = ""
            if hasattr(torch_directml, "get_device_name"):
                try:
                    name = torch_directml.get_device_name(i).lower()
                except Exception:  # pragma: no cover - best effort
                    name = ""
            if "660m" in name:  # Skip the integrated GPU
                continue
            if "6550m" in name:
                _device = torch_directml.device(i)
                break
            if _device is None:
                _device = torch_directml.device(i)
    if _device is not None:
        embeddings._DEVICE = _device
        embeddings.get_model.cache_clear()
except Exception:  # pragma: no cover - fall back silently
    pass

embed_identities = embeddings.embed_identities

def fetch_candidate_row(conn, customer_id, qvec):
    # Single candidate's vdist against qvec
    ensure_query_identity_table(conn)
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

def main(pairs_path: str | None = None, *, data_path: str | None = None):
    """Train the duplicate detection ranker.

    ``pairs_path`` may point to a pre-generated CSV/Parquet file of labelled
    query/candidate pairs.  When omitted, pairs are generated on the fly from
    ``data_path`` (a raw customer dataset) or directly from the database when
    ``data_path`` is ``None``.

    Supplying a ``pairs_path`` that does not exist returns a structured error
    which callers can surface to the user.
    """

    start = time.time()
    if pairs_path:
        if not os.path.exists(pairs_path):
            return {
                "success": False,
                "message": f"Training data not found: {pairs_path}",
            }
        df = load_dataframe(pairs_path)
    else:
        df = generate_pairs_df(input_path=data_path)

    # Prepare query dicts and canonical texts for batch embedding.  Iterating
    # over the dataframe with ``tqdm`` provides immediate feedback even for very
    # large datasets where converting to a list would appear to "hang".
    records: list[dict[str, object]] = []
    queries: list[dict[str, object]] = []
    texts: list[str] = []
    for row in tqdm(
        df.itertuples(index=False), total=len(df), desc="Preparing queries"
    ):
        r = row._asdict()
        records.append(r)
        q = dict(
            full_name=r["query_full_name"],
            dob=r.get("query_dob"),
            phone_e164=r.get("query_phone"),
            email_norm=r.get("query_email"),
            gov_id_norm=r.get("query_gov_id"),
            addr_line=r.get("query_addr"),
            city=r.get("query_city"),
            state=r.get("query_state"),
            postal_code=norm_postal_code(
                str(r.get("query_pc")) if r.get("query_pc") is not None else None
            ),
            country=r.get("query_ctry"),
        )
        queries.append(q)
        texts.append(
            canonical_identity_text(
                q["full_name"],
                q["dob"],
                q["phone_e164"],
                q["email_norm"],
                q["gov_id_norm"],
                q["addr_line"],
                q["city"],
                q["state"],
                q["postal_code"],
                q["country"],
            )
        )

    # Embedding large batches can take a while with no visible progress.  Break
    # the texts into chunks and show a second progress bar while embedding.
    def _chunks(seq: list[str], size: int):
        for i in range(0, len(seq), size):
            yield seq[i : i + size]

    # Reuse previously computed embeddings when available and complete.
    cache_path = (
        Path(pairs_path).with_suffix(".qvecs.npy")
        if pairs_path
        else Path("cached_qvecs.npy")
    )
    qvecs = None
    if cache_path.exists():
        try:
            qvecs = np.load(cache_path)
            if qvecs.shape[0] != len(texts):
                qvecs = None
        except Exception:  # pragma: no cover - corrupted cache
            qvecs = None
    if qvecs is None:
        qvec_list = []
        chunk_size = 64
        total_chunks = math.ceil(len(texts) / chunk_size)
        for chunk in tqdm(
            _chunks(texts, chunk_size), total=total_chunks, desc="Embedding"
        ):
            qvec_list.append(embed_identities(chunk))
        qvecs = (
            np.vstack(qvec_list)
            if qvec_list
            else np.empty((0, 512), dtype=np.float32)
        )
        np.save(cache_path, qvecs)
    else:
        print(f"Loaded {len(qvecs)} cached embeddings from {cache_path}")

    def _process(i):
        r = records[i]
        q = queries[i]
        qvec = qvecs[i]
        with get_conn() as conn:
            cand = fetch_candidate_row(conn, int(r["cand_customer_id"]), qvec)
        return feature_row(q, cand, cand["vdist"]), int(r["label"])

    with tqdm_joblib(tqdm(desc="Computing features", total=len(records))):
        results = Parallel(n_jobs=os.cpu_count())(
            delayed(_process)(i) for i in range(len(records))
        )
    if results:
        X, y = zip(*results)
    else:
        X, y = [], []
    X_arr = np.asarray(X)
    y_arr = np.asarray(y)

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        solver="liblinear",
        n_jobs=os.cpu_count(),
    )
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
        help="Path to CSV/Parquet file of labelled pairs (optional)",
    )
    parser.add_argument(
        "--data",
        dest="data_path",
        help="Raw customer dataset to generate training pairs when no pairs file is provided",
    )
    args = parser.parse_args()
    main(args.pairs_path, data_path=args.data_path)
