from fastapi.testclient import TestClient

from factorymark.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_stub_does_not_call_external_apis():
    r = client.post(
        "/api/analyze",
        json={"business_type": "café", "zone": "Palermo Soho"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["stub"] is True
    assert body["draft_post"]["status"] == "draft"
