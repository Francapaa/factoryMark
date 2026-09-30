"""Instagram v1: OAuth URL, estados, perfil solo-lectura. Cero llamadas reales."""

import httpx
from fastapi.testclient import TestClient

import instagram as ig
from config import settings
from main import app

client = TestClient(app)


def _auth():
    settings.auth_disabled = True


def _no_config(monkeypatch):
    monkeypatch.setattr(settings, "instagram_client_id", "")
    monkeypatch.setattr(settings, "instagram_redirect_uri", "")
    monkeypatch.setattr(settings, "instagram_client_secret", "")


def _config(monkeypatch):
    monkeypatch.setattr(settings, "instagram_client_id", "cid-123")
    monkeypatch.setattr(settings, "instagram_redirect_uri", "http://localhost:3000/cb")
    monkeypatch.setattr(settings, "instagram_client_secret", "shh")


def test_auth_url_requiere_config(monkeypatch):
    _auth()
    _no_config(monkeypatch)
    r = client.get("/api/instagram/auth-url")
    assert r.status_code == 400


def test_auth_url_flavor_instagram_scope_v1(monkeypatch):
    _auth()
    _config(monkeypatch)
    r = client.get("/api/instagram/auth-url")
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.startswith("https://www.instagram.com/oauth/authorize")
    assert "instagram_business_basic" in url
    assert "instagram_business_content_publish" not in url
    assert "client_secret" not in url


def test_status_desconectado_sin_conexion(monkeypatch):
    _auth()
    ig.clear_connection("dev-user")
    r = client.get("/api/instagram/status")
    assert r.status_code == 200
    assert r.json()["estado"] == "desconectado"


def test_profile_sin_conexion_es_409():
    _auth()
    ig.clear_connection("dev-user")
    r = client.get("/api/instagram/profile")
    assert r.status_code == 409


def test_callback_intercambia_code_y_guarda_conexion(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth/access_token" in str(request.url):
            return httpx.Response(200, json={"access_token": "tok-1", "user_id": "7"})
        if "graph.instagram.com/me" in str(request.url):
            return httpx.Response(
                200, json={"username": "cafecito", "followers_count": 120, "media_count": 34}
            )
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        "instagram.httpx.Client", lambda *a, **k: real_client(transport=transport)
    )
    r = client.get("/api/instagram/callback", params={"code": "abc", "state": "xyz"})
    assert r.status_code == 200
    assert r.json()["estado"] == "conectado"

    # El módulo jamás define endpoints de publicación ni insights.
    assert not hasattr(ig, "publish_post")
    assert not hasattr(ig, "fetch_insights")
    for path in ("media_publish", "insights", "content_publishing"):
        assert path not in ig.GRAPH_BASE


def test_disconnect_limpia_estado():
    _auth()
    ig.save_connection("dev-user", "tok-x", "cafecito")
    r = client.delete("/api/instagram/disconnect")
    assert r.status_code == 200
    assert r.json()["estado"] == "desconectado"
    assert client.get("/api/instagram/status").json()["estado"] == "desconectado"
