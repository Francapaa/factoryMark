"""Tests del onboarding: resolve, save/mine, gate 409, photo proxy. Cero red real."""

import os

import pytest
from fastapi.testclient import TestClient

import db
from api import businesses
from auth import CurrentUser, get_current_user
from config import settings
from main import app
from state import Anchor
from tools import places
from tools.places import AnchorNotFoundError

client = TestClient(app)


@pytest.fixture
def anon():
    """Auth desactivada (dev): user fijo `dev-user`."""
    old = settings.auth_disabled
    settings.auth_disabled = True
    yield
    settings.auth_disabled = old


@pytest.fixture
def as_user():
    """Override de auth para simular distintos dueños."""

    def _as(user_id: str):
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=user_id)

    yield _as
    app.dependency_overrides.clear()


def _saved(owner_id: str = "dev-user") -> dict:
    return {
        "id": "b1",
        "owner_id": owner_id,
        "name": "Café Martínez",
        "business_type": "café de especialidad",
        "sales_channel": "local",
        "zone": "Palermo Soho",
        "anchor_place_id": "anchor1",
        "anchor_snapshot": {"address": "Calle Falsa 123"},
        "brand_kit": None,
        "created_at": None,
        "updated_at": None,
    }


# --- resolve ---


def test_resolve_rechaza_input_vacio(anon):
    r = client.post("/api/businesses/resolve", json={"name": "", "zone": "Palermo"})
    assert r.status_code == 422


def test_resolve_sin_key_no_inventa(anon, monkeypatch):
    monkeypatch.setattr(settings, "google_places_api_key", "")
    r = client.post("/api/businesses/resolve", json={"name": "Café X", "zone": "Palermo"})
    assert r.status_code == 400


def test_resolve_no_encontrado_404(anon, monkeypatch):
    def boom(name, zone, **kwargs):
        raise AnchorNotFoundError("No encontramos 'X' en 'Y' en Google Maps. Verificá el nombre.")

    monkeypatch.setattr(places, "resolve_anchor", boom)
    r = client.post("/api/businesses/resolve", json={"name": "No Existe", "zone": "Palermo"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "negocio_no_encontrado"


def test_resolve_ok_devuelve_ancla_y_maps_link(anon, monkeypatch):
    monkeypatch.setattr(
        places,
        "resolve_anchor",
        lambda name, zone, **kwargs: Anchor(
            place_id="anchor1",
            name="Café Martínez",
            address="Calle Falsa 123",
            latitude=-34.58,
            longitude=-58.43,
        ),
    )
    monkeypatch.setattr(
        places,
        "fetch_place_details",
        lambda place_id, **kwargs: {
            "rating": 4.5,
            "opening_hours": ["lunes: 8–20"],
            "photos": ["places/anchor1/photos/ref1"],
            "reviews": [],
        },
    )
    r = client.post("/api/businesses/resolve", json={"name": "Café Martínez", "zone": "Palermo"})
    assert r.status_code == 200
    body = r.json()
    assert body["place_id"] == "anchor1"
    assert body["photo_ref"] == "places/anchor1/photos/ref1"
    assert body["maps_url"] == "https://www.google.com/maps/search/?api=1&query_place_id=anchor1"
    assert "GOOGLE_PLACES_API_KEY" not in r.text


# --- save / mine ---


def test_mine_sin_negocio_404(as_user, monkeypatch):
    as_user("user-a")
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: None)
    r = client.get("/api/businesses/mine")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "sin_negocio"


def test_save_y_read_roundtrip_y_aislamiento(as_user):
    store: dict[str, dict] = {}

    def fake_save(owner_id: str, **fields):
        row = {"id": f"id-{owner_id}", "owner_id": owner_id, **fields}
        row.setdefault("brand_kit", None)
        row.setdefault("created_at", None)
        row.setdefault("updated_at", None)
        store[owner_id] = row
        return row

    monkeypatch_save = fake_save
    import api.businesses as biz

    orig_save, orig_get = db.save_my_business, db.get_my_business
    db.save_my_business = monkeypatch_save  # type: ignore[assignment]
    db.get_my_business = lambda owner_id: store.get(owner_id)  # type: ignore[assignment]
    try:
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
        assert client.get("/api/businesses/mine").status_code == 404  # aislamiento
        payload_b = dict(payload, name="Otro Café", anchor_place_id="anchor2")
        assert client.post("/api/businesses", json=payload_b).status_code == 200

        as_user("user-a")
        assert client.get("/api/businesses/mine").json()["name"] == "Café Martínez"
        _ = biz  # el router usa db.* en tiempo de request
    finally:
        db.save_my_business, db.get_my_business = orig_save, orig_get


def test_db_sin_config_falla_claro(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.get_my_business("x")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.save_my_business(
            "x",
            name="n",
            business_type="t",
            sales_channel="local",
            zone="z",
            anchor_place_id="p",
            anchor_snapshot={},
        )


def test_health_reporta_db_configured(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    assert client.get("/health").json()["db_configured"] is False
    monkeypatch.setattr(settings, "database_url", "postgresql://ejemplo/db")
    assert client.get("/health").json()["db_configured"] is True


# --- gate /api/analyze ---


def test_analyze_sin_onboarding_409(anon, monkeypatch):
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: None)
    r = client.post(
        "/api/analyze",
        json={
            "business_name": "Café Ejemplo",
            "business_type": "café",
            "zone": "Palermo Soho",
            "sales_channel": "local",
        },
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "onboarding_incompleto"


def test_analyze_con_negocio_usa_datos_guardados(anon, monkeypatch):
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
    seen = {}

    from api import analysis as analysis_module

    def fake_run(name, btype, zone, channel="local"):
        seen.update(name=name, btype=btype, zone=zone, channel=channel)
        return {
            "competitors": [],
            "clusters": [],
            "opportunities": [],
            "draft_post": None,
            "meta": {},
        }

    monkeypatch.setattr(analysis_module, "run_analysis", fake_run)
    r = client.post(
        "/api/analyze",
        json={
            "business_name": "Otro tipeado (sin confirmar)",
            "business_type": "bar",
            "zone": "Belgrano",
            "sales_channel": "online",
        },
    )
    assert r.status_code == 200
    # El run usa lo guardado/confirmado, no el input sin confirmar.
    assert seen == {
        "name": "Café Martínez",
        "btype": "café de especialidad",
        "zone": "Palermo Soho",
        "channel": "local",
    }


# --- photo proxy ---


def test_photo_rechaza_urls_arbitrarias(anon):
    for bad in ["https://evil.com/foto.jpg", "http://x/y", "../etc/passwd", "places"]:
        r = client.get("/api/businesses/photo", params={"photo_ref": bad})
        assert r.status_code in (400, 422), bad


def test_photo_ok_sirve_bytes_sin_key(anon, monkeypatch):
    monkeypatch.setattr(settings, "google_places_api_key", "k")
    monkeypatch.setattr(businesses, "fetch_photo_bytes", lambda ref: (b"fake-bytes", "image/jpeg"))
    r = client.get("/api/businesses/photo", params={"photo_ref": "places/a/photos/b"})
    assert r.status_code == 200
    assert r.content == b"fake-bytes"
    assert "GOOGLE_PLACES_API_KEY" not in r.text


# --- storage real (solo con DATABASE_URL efímera) ---


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requiere Postgres efímera")
def test_storage_roundtrip_postgres_real():
    from pathlib import Path

    import psycopg

    schema = Path(__file__).resolve().parents[1] / "schema.sql"
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute(schema.read_text(encoding="utf-8"))
        conn.commit()
    saved = db.save_my_business(
        "owner-test",
        name="Café Test",
        business_type="café",
        sales_channel="local",
        zone="Palermo",
        anchor_place_id="p-test",
        anchor_snapshot={"address": "Calle 1"},
    )
    assert saved["anchor_place_id"] == "p-test"
    assert db.get_my_business("owner-test")["name"] == "Café Test"
    assert db.get_my_business("otro-owner") is None
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("DELETE FROM app.negocios WHERE owner_id = 'owner-test'")
        conn.commit()
