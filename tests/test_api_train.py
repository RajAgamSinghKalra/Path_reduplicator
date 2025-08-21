import pathlib

from fastapi.testclient import TestClient

from app.api.main import app


def test_train_endpoint_cors_and_missing_file(tmp_path: pathlib.Path):
    """Train endpoint should return a helpful error and CORS headers."""

    client = TestClient(app)
    missing = tmp_path / "missing.csv"
    resp = client.post(
        "/train",
        json={"csv_path": str(missing)},
        headers={"Origin": "http://example.com"},
    )

    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"
    body = resp.json()
    assert body["success"] is False
    assert "Training data not found" in body["message"]

