"""Health + analyze E2E (DB real, stub sin keys). Sin mocks de storage."""

from conftest import REQUIRES_DB
from fastapi.testclient import TestClient

from auth import CurrentUser, get_current_user
from config import settings
from main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@REQUIRES_DB
def test_analyze_e2e_stub_con_negocio_real(db_isolated, monkeypatch, tmp_path):
    """Guarda negocio real, corre pipeline stub (sin keys), aserta contrato.

    Mutación: si se rompe el orden researcher->publisher, trace cambia y falla.
    """
    from tools import places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(settings, "auth_disabled", True)
    monkeypatch.setattr(settings, "google_places_api_key", "")
    monkeypatch.setattr(settings, "tavily_api_key", "")
    monkeypatch.setattr(places_mod, "default_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="dev-user")
    try:
        import db

        db.save_my_business(
            "dev-user", name="Café Ejemplo", business_type="café",
            sales_channel="local", zone="Palermo Soho",
            anchor_place_id="anchor1", anchor_snapshot={},
        )
        r = client.post(
            "/api/analyze",
            json={"business_name": "Café Ejemplo", "business_type": "café",
                  "zone": "Palermo Soho", "sales_channel": "local"},
        )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["stub"] is True
    assert body["draft_post"]["status"] == "draft"
    assert len(body["competitors"]) >= 1
    assert len(body["opportunities"]) >= 1


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
        json={"business_name": "Café Ejemplo", "business_type": "café",
              "zone": "Palermo Soho", "sales_channel": "redes"},
    )
    assert r.status_code == 422
