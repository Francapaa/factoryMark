from fastapi.testclient import TestClient

from config import settings
from main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_stub_does_not_call_external_apis(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", True)
    r = client.post(
        "/api/analyze",
        json={
            "business_name": "Café Ejemplo",
            "business_type": "café",
            "zone": "Palermo Soho",
            "sales_channel": "local",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["stub"] is True
    assert body["draft_post"]["status"] == "draft"


def test_analyze_rechaza_sin_business_name(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", True)
    r = client.post(
        "/api/analyze",
        json={"business_type": "café", "zone": "Palermo Soho", "sales_channel": "local"},
    )
    assert r.status_code == 422


def test_analyze_rechaza_canal_invalido(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", True)
    r = client.post(
        "/api/analyze",
        json={
            "business_name": "Café Ejemplo",
            "business_type": "café",
            "zone": "Palermo Soho",
            "sales_channel": "redes",
        },
    )
    assert r.status_code == 422
