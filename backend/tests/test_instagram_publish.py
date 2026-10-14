"""Instagram v2: publicación inmediata + programadas + worker. Cero llamadas reales."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

import instagram as ig
from api import instagram as igapi
from config import settings
from main import app

client = TestClient(app)
IMG = "https://cdn.mi-local.com/post.jpg"


@pytest.fixture(autouse=True)
def _isolation(monkeypatch):
    settings.auth_disabled = True
    monkeypatch.setattr(settings, "instagram_client_id", "cid-123")
    monkeypatch.setattr(settings, "instagram_redirect_uri", "http://localhost:3000/cb")
    monkeypatch.setattr(settings, "instagram_client_secret", "shh")
    monkeypatch.setattr(settings, "database_url", "")
    ig.clear_connection("dev-user")
    igapi._mem_posts.clear()
    yield
    ig.clear_connection("dev-user")
    igapi._mem_posts.clear()


def _mock_graph(monkeypatch, status_code: str = "FINISHED"):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "media_publish" in url:
            return httpx.Response(200, json={"id": "media-1"})
        if url.rstrip("/").endswith("/me/media"):
            return httpx.Response(200, json={"id": "container-1"})
        if "content_publishing_limit" in url:
            return httpx.Response(200, json={"quota_usage": 3, "rate_limit_settings": {}})
        if "/container-1" in url:
            return httpx.Response(200, json={"status_code": status_code})
        if "graph.instagram.com/me" in url:
            return httpx.Response(200, json={"username": "cafecito"})
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        "instagram.httpx.Client", lambda *a, **k: real_client(transport=transport)
    )


def _connect(scopes: str = ",".join(ig.V2_SCOPES)):
    ig.save_connection("dev-user", "tok-long", "cafecito", scopes=scopes)


def test_publish_photo_now_orquesta_container_poll_publish(monkeypatch):
    _mock_graph(monkeypatch)
    result = ig.publish_photo_now("tok", IMG, "Promo de tarde", sleep_s=0)
    assert result == {"container_id": "container-1", "media_id": "media-1"}


def test_publish_photo_now_falla_si_container_error(monkeypatch):
    _mock_graph(monkeypatch, status_code="ERROR")
    try:
        ig.publish_photo_now("tok", IMG, "x", sleep_s=0)
    except RuntimeError as exc:
        assert "ERROR" in str(exc)
    else:
        raise AssertionError("Debería fallar con container en ERROR")


def test_publish_endpoint_requiere_conexion():
    r = client.post("/api/instagram/publish", json={"image_url": IMG, "caption": "Hola"})
    assert r.status_code == 409


def test_publish_endpoint_requiere_scope(monkeypatch):
    _connect(scopes=ig.V1_SCOPE)  # conexión vieja, sin permiso de publicación
    r = client.post("/api/instagram/publish", json={"image_url": IMG, "caption": "Hola"})
    assert r.status_code == 409
    assert "permiso" in r.json()["detail"]


def test_publish_endpoint_publica(monkeypatch):
    _connect()
    _mock_graph(monkeypatch)
    r = client.post("/api/instagram/publish", json={"image_url": IMG, "caption": "Promo ☕"})
    assert r.status_code == 200, r.text
    assert r.json() == {"estado": "publicado", "media_id": "media-1", "container_id": "container-1"}


def test_publish_endpoint_valida_url():
    _connect()
    r = client.post("/api/instagram/publish", json={"image_url": "nope", "caption": "x"})
    assert r.status_code == 400


def test_limit_endpoint(monkeypatch):
    _connect()
    _mock_graph(monkeypatch)
    r = client.get("/api/instagram/limit")
    assert r.status_code == 200
    assert r.json()["quota_usage"] == 3


def _future(minutes: int = 60) -> str:
    return (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat()


def test_scheduled_crud(monkeypatch):
    _connect()
    # Crear
    r = client.post(
        "/api/instagram/scheduled",
        json={"image_url": IMG, "caption": "Tarde ☕", "programada_para": _future()},
    )
    assert r.status_code == 200, r.text
    post = r.json()
    assert post["estado"] == "programado"
    # Listar
    listed = client.get("/api/instagram/scheduled").json()
    assert len(listed) == 1 and listed[0]["id"] == post["id"]
    # Pasado → 400
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    r = client.post(
        "/api/instagram/scheduled",
        json={"image_url": IMG, "caption": "x", "programada_para": past},
    )
    assert r.status_code == 400
    # Cancelar
    r = client.delete(f"/api/instagram/scheduled/{post['id']}")
    assert r.status_code == 200
    assert r.json()["estado"] == "rechazado"
    # Cancelar de nuevo → 409 (ya no está pendiente)
    r = client.delete(f"/api/instagram/scheduled/{post['id']}")
    assert r.status_code == 409


def test_scheduled_publish_now_y_run_due(monkeypatch):
    _connect()
    _mock_graph(monkeypatch)
    # Una futura (publish-now la adelanta) y una vencida a mano en memoria.
    r = client.post(
        "/api/instagram/scheduled",
        json={"image_url": IMG, "caption": "Futura", "programada_para": _future()},
    )
    future_id = r.json()["id"]
    past_id = "00000000-0000-0000-0000-000000000001"
    igapi._mem_posts.setdefault("dev-user", {})[past_id] = {
        "id": past_id,
        "owner_id": "dev-user",
        "copy_text": "",
        "hashtags": [],
        "image_url": IMG,
        "caption": "Vencida",
        "estado": "programado",
        "programada_para": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        "container_id": None,
        "external_id": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "published_at": None,
    }
    # Publish-now sobre la futura
    r = client.post(f"/api/instagram/scheduled/{future_id}/publish-now")
    assert r.status_code == 200, r.text
    assert r.json()["media_id"] == "media-1"
    # Run-due publica solo la vencida
    r = client.post("/api/instagram/scheduled/run-due")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"revisados": 1, "publicados": 1, "errores": []}
    # Segunda corrida: nada vencido
    r = client.post("/api/instagram/scheduled/run-due")
    assert r.json()["revisados"] == 0


def test_run_due_marca_error_si_meta_falla(monkeypatch):
    _connect()

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.rstrip("/").endswith("/me/media"):
            return httpx.Response(400, json={"error": {"message": "bad image"}})
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        "instagram.httpx.Client", lambda *a, **k: real_client(transport=transport)
    )
    past_id = "00000000-0000-0000-0000-000000000002"
    igapi._mem_posts.setdefault("dev-user", {})[past_id] = {
        "id": past_id,
        "owner_id": "dev-user",
        "copy_text": "",
        "hashtags": [],
        "image_url": IMG,
        "caption": "Rota",
        "estado": "programado",
        "programada_para": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        "container_id": None,
        "external_id": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "published_at": None,
    }
    r = client.post("/api/instagram/scheduled/run-due")
    assert r.status_code == 200
    body = r.json()
    assert body["publicados"] == 0 and len(body["errores"]) == 1
    listed = client.get("/api/instagram/scheduled").json()
    assert listed[0]["estado"] == "error"
    assert listed[0]["error"]
