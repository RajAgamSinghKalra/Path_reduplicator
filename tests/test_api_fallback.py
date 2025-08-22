import sys
import pathlib
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import app.api.main as main
import app.deduper as deduper
import app.model_store as model_store


class DummyConn:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


def test_api_uses_rule_based_classifier(monkeypatch):
    """Fallback model should still return a high score via the API."""

    Path("model.bin").unlink(missing_ok=True)
    model_store._CACHE.clear()

    client = TestClient(main.app)

    monkeypatch.setattr(deduper, "embed_identity", lambda text: [0.0] * 512)
    monkeypatch.setattr(deduper, "get_conn", lambda: DummyConn())

    def fake_topk(conn, vec, k):
        return [
            (
                1,
                0.1,
                "John Doe",
                date.fromisoformat("1980-01-01"),
                "100",
                "john@example.com",
                "ID123",
                "123 Street",
                "Metropolis",
                "NY",
                "123456",
            )
        ]

    monkeypatch.setattr(deduper, "topk_by_vector", fake_topk)

    payload = {
        "full_name": "John Doe",
        "date_of_birth": "1980-01-01",
        "phone": "+100",
        "email": "john@example.com",
        "government_id": "ID123",
        "address_line": "123 Street",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "123456",
        "country": "IN",
    }

    resp = client.post("/dedupe/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_duplicate"] is True
    assert data["score"] > 0.95
    assert data["best_match"]["government_id"] == "ID123"
