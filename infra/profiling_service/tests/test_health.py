from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_ping():
    r = client.get("/v1/profile/ping")
    assert r.status_code == 200
    assert "profiling service" in r.json().get("message")
