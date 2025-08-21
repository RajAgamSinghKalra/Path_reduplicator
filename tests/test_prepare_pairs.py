import pandas as pd
from pathlib import Path
from training import prepare_pairs


class DummyConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class DummyLOB:
    """Simple stand-in for an Oracle LOB object.

    The object defines a ``read`` method returning the underlying value and
    deliberately raises ``TypeError`` for comparisons to mimic the behaviour of
    ``oracledb.LOB`` objects when pandas attempts to sort them.
    """

    def __init__(self, value: str):
        self._value = value

    def read(self) -> str:
        return self._value

    def __lt__(self, other):  # pragma: no cover - used only for failure mode
        raise TypeError("LOB objects are not orderable")


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


def test_handles_lob_identity_text(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "CUSTOMER_ID": [1, 2],
            "IDENTITY_TEXT": [DummyLOB("a"), DummyLOB("a")],
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
