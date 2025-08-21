import pathlib

from training import train_ranker


def test_missing_training_data(tmp_path: pathlib.Path):
    """Ensure a helpful response when the training data file is absent."""

    missing = tmp_path / "does-not-exist.csv"
    result = train_ranker.main(pairs_path=str(missing))
    assert result["success"] is False
    assert "Training data not found" in result["message"]


def test_train_from_raw_data(monkeypatch):
    """Training should work when only raw customer data is provided."""

    import json
    import pandas as pd
    import numpy as np

    data_path = pathlib.Path("dataset/sample_customers.csv")
    df = pd.read_csv(data_path)
    df["identity_vec"] = df["identity_vec"].apply(json.loads)
    records = {int(r["customer_id"]): r for r in df.to_dict("records")}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_fetch(conn, customer_id, qvec):
        r = records[customer_id]
        vec = np.asarray(r["identity_vec"], dtype=float)
        vdist = float(np.linalg.norm(vec - qvec))
        return {
            "full_name": r["full_name"],
            "dob": r["dob"],
            "phone_e164": str(r["phone_e164"]),
            "email_norm": r["email_norm"],
            "gov_id_norm": r["gov_id_norm"],
            "addr_line": r["addr_line"],
            "city": r["city"],
            "state": r["state"],
            "postal_code": str(r["postal_code"]),
            "vdist": vdist,
        }

    monkeypatch.setattr(train_ranker, "fetch_candidate_row", fake_fetch)
    monkeypatch.setattr(train_ranker, "get_conn", lambda: DummyConn())
    monkeypatch.setattr(
        train_ranker,
        "embed_identities",
        lambda texts: np.zeros((len(texts), 512), dtype=np.float32),
    )

    result = train_ranker.main(data_path=str(data_path))
    assert result["success"] is True
    assert result["details"]["pairs_processed"] > 0

