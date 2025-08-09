import sys, pathlib

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
    def fake_train(csv_path):
        called["csv"] = csv_path
    monkeypatch.setattr(main, "train_ranker", fake_train)
    resp = client.post("/train", json={"pairs_csv": "foo.csv"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "trained"
    assert called["csv"] == "foo.csv"
