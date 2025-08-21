import pandas as pd
from pathlib import Path
from training import prepare_pairs


class DummyConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_handles_uppercase_columns(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "CUSTOMER_ID": [1, 2],
            "IDENTITY_TEXT": ["a", "a"],
        }
    )

    monkeypatch.setattr(prepare_pairs, "get_conn", lambda: DummyConn())
    monkeypatch.setattr(pd, "read_sql", lambda sql, conn: df)
    monkeypatch.setattr(prepare_pairs, "_row_to_query", lambda row: {})
    monkeypatch.setattr(prepare_pairs, "_query_vector", lambda row: [0.0])
    monkeypatch.setattr(
        prepare_pairs,
        "_hard_negative",
        lambda conn, qvec, exclude_ids, k=20: None,
    )

    out = tmp_path / "pairs.csv"
    prepare_pairs.main(str(out))
    result = pd.read_csv(out)
    assert set(result["cand_customer_id"]) == {1, 2}
    assert (result["label"] == 1).all()
