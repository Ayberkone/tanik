from fastapi.testclient import TestClient

from tanik_inference.main import app


def test_health_returns_ok():
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["iris_engine"].startswith("open-iris/")
    assert body["fingerprint_engine"].startswith("sourceafis/")
    assert body["calibration_status"] == "placeholder"
    assert body["version"] == "0.1.0"
