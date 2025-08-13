import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import app.api.main as main

client = TestClient(main.app)

def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_train_endpoint(monkeypatch):
    called = {}

    def fake_train(path):
        called["path"] = path

    monkeypatch.setattr(main, "train_ranker", fake_train)
    resp = client.post("/train", json={"csv_path": "foo.csv"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "trained"
    assert called["path"] == "foo.csv"


def test_dedupe_field_aliases(monkeypatch):
    sample = {
        "customer_id": 1,
        "vdist": 0.12,
        "full_name": "John Doe",
        "dob": "1980-01-01",
        "phone_e164": "+12025550123",
        "email_norm": "john@example.com",
        "gov_id_norm": "ID123",
        "addr_line": "123 Street",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "123456",
        "score": 0.95,
    }

    def fake_check(payload):
        return {
            "is_duplicate": True,
            "score": 0.95,
            "best_match": sample,
            "candidates": [sample],
        }

    monkeypatch.setattr(main, "check_duplicate", fake_check)

    payload = {
        "full_name": "Jane",
        "date_of_birth": "1985-05-05",
        "phone": "+1987654321",
        "email": "jane@example.com",
        "government_id": "ID999",
        "address_line": "321 Ave",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "654321",
        "country": "IN",
    }

    resp = client.post("/dedupe/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["threshold"] == main.Config.THRESHOLD
    assert data["best_match"]["name"] == "John Doe"
    assert data["best_match"]["vector_distance"] == 0.12
