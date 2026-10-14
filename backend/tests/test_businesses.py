"""Onboarding E2E: resolve (HTTP borde real) + save/mine/gate (Postgres real).

Mutaciones que deben romper estos tests:
- quitar _PHOTO_REF_RE -> test_photo_rechaza_urls_arbitrarias falla 200 en vez de 400
- romper upsert ON CONFLICT -> test_save_y_read_roundtrip_y_aislamiento falla
- romper gate onboarding_incompleto -> test_analyze_sin_onboarding_409 falla
"""

import os

import httpx
import pytest
from conftest import REQUIRES_DB
from fastapi.testclient import TestClient

import db
from auth import CurrentUser, get_current_user
from config import settings
from main import app
from tools import places

client = TestClient(app)


@pytest.fixture
def anon():
    old = settings.auth_disabled
    settings.auth_disabled = True
    yield
    settings.auth_disabled = old


@pytest.fixture
def as_user():
    def _as(user_id: str):
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=user_id)

    yield _as
    app.dependency_overrides.clear()


def _mock_places_http(monkeypatch, tmp_path, anchor_places, details=None):
    """Borde HTTP real simulado: intercepta httpx.Client, no mockea resolve_anchor."""
    monkeypatch.setattr(settings, "google_places_api_key", "k")
    monkeypatch.setattr(places, "default_cache_dir", lambda: tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "places:searchText" in url:
            return httpx.Response(200, json={"places": anchor_places})
        if "/places/" in url:
            pid = url.rstrip("/").split("/")[-1].split("?")[0]
            payload = (details or {}).get(pid, {"id": pid, "reviews": []})
            return httpx.Response(200, json=payload)
        raise AssertionError(f"URL inesperada: {url}")

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: real_client(transport=transport))


def _anchor(name="Café Martínez"):
    return {
        "id": "anchor1",
        "displayName": {"text": name},
        "formattedAddress": "Calle Falsa 123",
        "location": {"latitude": -34.58, "longitude": -58.43},
    }


# --- resolve: endpoint real + HTTP borde simulado ---


def test_resolve_rechaza_input_vacio(anon):
    r = client.post("/api/businesses/resolve", json={"name": "", "zone": "Palermo"})
    assert r.status_code == 422


def test_resolve_sin_key_no_inventa(anon, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "google_places_api_key", "")
    monkeypatch.setattr(places, "default_cache_dir", lambda: tmp_path)
    r = client.post("/api/businesses/resolve", json={"name": "Café X", "zone": "Palermo"})
    assert r.status_code == 400


def test_resolve_no_encontrado_404(anon, monkeypatch, tmp_path):
    _mock_places_http(monkeypatch, tmp_path, anchor_places=[])
    r = client.post("/api/businesses/resolve", json={"name": "No Existe", "zone": "Palermo"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "negocio_no_encontrado"


def test_resolve_ok_devuelve_ancla_y_maps_link(anon, monkeypatch, tmp_path):
    _mock_places_http(
        monkeypatch,
        tmp_path,
        anchor_places=[_anchor()],
        details={"anchor1": {"id": "anchor1", "rating": 4.5,
                             "regularOpeningHours": {"weekdayDescriptions": ["lunes: 8–20"]},
                             "photos": [{"name": "places/anchor1/photos/ref1"}],
                             "reviews": []}},
    )
    r = client.post("/api/businesses/resolve", json={"name": "Café Martínez", "zone": "Palermo"})
    assert r.status_code == 200
    body = r.json()
    assert body["place_id"] == "anchor1"
    assert body["photo_ref"] == "places/anchor1/photos/ref1"
    assert body["maps_url"] == "https://www.google.com/maps/search/?api=1&query_place_id=anchor1"
    assert "GOOGLE_PLACES_API_KEY" not in r.text


# --- save / mine: Postgres real, aislamiento por owner ---


@REQUIRES_DB
def test_mine_sin_negocio_404(as_user, db_isolated):
    as_user("user-a")
    r = client.get("/api/businesses/mine")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "sin_negocio"


@REQUIRES_DB
def test_save_y_read_roundtrip_y_aislamiento(as_user, db_isolated):
    payload = {
        "name": "Café Martínez",
        "business_type": "café",
        "sales_channel": "local",
        "zone": "Palermo",
        "anchor_place_id": "anchor1",
        "anchor_snapshot": {"address": "Calle Falsa 123"},
    }
    as_user("user-a")
    assert client.post("/api/businesses", json=payload).status_code == 200
    mine_a = client.get("/api/businesses/mine")
    assert mine_a.status_code == 200
    assert mine_a.json()["anchor_place_id"] == "anchor1"

    as_user("user-b")
    assert client.get("/api/businesses/mine").status_code == 404
    payload_b = dict(payload, name="Otro Café", anchor_place_id="anchor2")
    assert client.post("/api/businesses", json=payload_b).status_code == 200

    as_user("user-a")
    assert client.get("/api/businesses/mine").json()["name"] == "Café Martínez"


def test_db_sin_config_falla_claro(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.get_my_business("x")


def test_health_reporta_db_configured(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    assert client.get("/health").json()["db_configured"] is False
    monkeypatch.setattr(settings, "database_url", "postgresql://ejemplo/db")
    assert client.get("/health").json()["db_configured"] is True


# --- gate /api/analyze: DB real, run real (stub sin keys) ---


@REQUIRES_DB
def test_analyze_sin_onboarding_409(as_user, db_isolated):
    as_user("user-a")
    r = client.post(
        "/api/analyze",
        json={"business_name": "Café Ejemplo", "business_type": "café",
              "zone": "Palermo Soho", "sales_channel": "local"},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "onboarding_incompleto"


@REQUIRES_DB
def test_analyze_con_negocio_ignora_input_sin_confirmar(as_user, db_isolated, monkeypatch, tmp_path):
    """E2E: guarda negocio real, analiza con input distinto, el run usa lo guardado.

    Mutación: si analyze usara req.business_name en vez de saved["name"],
    el handler HTTP vería 'Otro tipeado' y devolvería 404.
    """
    as_user("dev-user")
    saved_payload = {
        "name": "Café Martínez",
        "business_type": "café de especialidad",
        "sales_channel": "local",
        "zone": "Palermo Soho",
        "anchor_place_id": "anchor1",
        "anchor_snapshot": {"address": "Calle Falsa 123"},
    }
    assert client.post("/api/businesses", json=saved_payload).status_code == 200

    monkeypatch.setattr(settings, "google_places_api_key", "k")
    monkeypatch.setattr(settings, "tavily_api_key", "")
    monkeypatch.setattr(places, "default_cache_dir", lambda: tmp_path)
    from tools import tavily as tavily_mod
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "places:searchText" in url:
            body = request.read().decode()
            assert "Café Martínez" in body, f"el run debe usar lo guardado, no el input: {body}"
            if " en " not in body:
                return httpx.Response(200, json={"places": [_anchor()]})
            return httpx.Response(200, json={"places": [_anchor(), {
                "id": "p-near", "displayName": {"text": "Café Cercano"},
                "rating": 4.5, "userRatingCount": 10, "formattedAddress": "C1",
                "location": {"latitude": -34.581, "longitude": -58.431}}]})
        if "/places/" in url:
            return httpx.Response(200, json={"id": "x", "reviews": []})
        raise AssertionError(f"URL inesperada: {url}")

    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: real_client(transport=httpx.MockTransport(handler)))

    r = client.post(
        "/api/analyze",
        json={"business_name": "Otro tipeado (sin confirmar)", "business_type": "bar",
              "zone": "Belgrano", "sales_channel": "local"},
    )
    assert r.status_code == 200
    assert r.json()["meta"]["stub"] is False


# --- photo proxy: borde httpx.get, no mock de fetch_photo_bytes ---


def test_photo_rechaza_urls_arbitrarias(anon):
    for bad in ["https://evil.com/foto.jpg", "http://x/y", "../etc/passwd", "places"]:
        r = client.get("/api/businesses/photo", params={"photo_ref": bad})
        assert r.status_code in (400, 422), bad


def test_photo_ok_sirve_bytes_sin_exponer_key(anon, monkeypatch):
    monkeypatch.setattr(settings, "google_places_api_key", "k")
    fake = httpx.Response(
        200, content=b"fake-bytes", headers={"content-type": "image/jpeg"},
        request=httpx.Request("GET", "https://places.googleapis.com/v1/places/a/photos/b/media"),
    )
    monkeypatch.setattr(httpx, "get", lambda *a, **k: fake)
    r = client.get("/api/businesses/photo", params={"photo_ref": "places/a/photos/b"})
    assert r.status_code == 200
    assert r.content == b"fake-bytes"
    assert "GOOGLE_PLACES_API_KEY" not in str(r.headers)


# --- storage real (solo con DATABASE_URL efímera) ---


@REQUIRES_DB
def test_storage_roundtrip_postgres_real(db_isolated):
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    command.upgrade(cfg, "head")
    saved = db.save_my_business(
        "owner-test", name="Café Test", business_type="café", sales_channel="local",
        zone="Palermo", anchor_place_id="p-test", anchor_snapshot={"address": "Calle 1"},
    )
    assert saved["anchor_place_id"] == "p-test"
    assert db.get_my_business("owner-test")["name"] == "Café Test"
    assert db.get_my_business("otro-owner") is None
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("DELETE FROM app.negocios WHERE owner_id = 'owner-test'")
        conn.commit()
