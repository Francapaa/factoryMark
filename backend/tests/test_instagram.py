"""Instagram v2: OAuth con scopes de publicación, estados, perfil. Cero llamadas reales."""

import httpx
from fastapi.testclient import TestClient

import instagram as ig
from api import instagram as igapi
from config import settings
from main import app

client = TestClient(app)


def _auth():
    settings.auth_disabled = True


def _no_config(monkeypatch):
    monkeypatch.setattr(settings, "instagram_client_id", "")
    monkeypatch.setattr(settings, "instagram_redirect_uri", "")
    monkeypatch.setattr(settings, "instagram_client_secret", "")
    monkeypatch.setattr(settings, "database_url", "")


def _config(monkeypatch):
    monkeypatch.setattr(settings, "instagram_client_id", "cid-123")
    monkeypatch.setattr(settings, "instagram_redirect_uri", "http://localhost:3000/cb")
    monkeypatch.setattr(settings, "instagram_client_secret", "shh")
    monkeypatch.setattr(settings, "database_url", "")
    monkeypatch.setattr(settings, "token_encryption_key", "")


def _mock_client(monkeypatch, long_lived_ok: bool = True):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "oauth/access_token" in url:
            return httpx.Response(200, json={"access_token": "short-1", "user_id": "7"})
        if "refresh_access_token" in url:
            return httpx.Response(200, json={"access_token": "long-2", "expires_in": 5184000})
        if "graph.instagram.com/access_token" in url:
            if long_lived_ok:
                return httpx.Response(200, json={"access_token": "long-1", "expires_in": 5184000})
            return httpx.Response(400, json={"error": "no"})
        if "graph.instagram.com/me" in url:
            return httpx.Response(
                200,
                json={
                    "id": "9001",
                    "username": "cafecito",
                    "followers_count": 120,
                    "media_count": 34,
                },
            )
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        "instagram.httpx.Client", lambda *a, **k: real_client(transport=transport)
    )


def test_auth_url_requiere_config(monkeypatch):
    _auth()
    _no_config(monkeypatch)
    r = client.get("/api/instagram/auth-url")
    assert r.status_code == 400


def test_auth_url_pide_scopes_v2_y_state(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")
    r = client.get("/api/instagram/auth-url")
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.startswith("https://www.instagram.com/oauth/authorize")
    assert "instagram_business_basic" in url
    assert "instagram_business_content_publish" in url
    assert "client_secret" not in url
    assert "state=" in url


def test_callback_state_invalido_es_400(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")
    client.get("/api/instagram/auth-url")  # genera un state pendiente
    r = client.get("/api/instagram/callback", params={"code": "abc", "state": "trucho"})
    assert r.status_code == 400


def test_status_desconectado_sin_conexion(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")
    igapi._mem_posts.clear()
    r = client.get("/api/instagram/status")
    assert r.status_code == 200
    assert r.json()["estado"] == "desconectado"


def test_profile_sin_conexion_es_409(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")
    r = client.get("/api/instagram/profile")
    assert r.status_code == 409


def _do_callback(monkeypatch, long_lived_ok: bool = True) -> dict:
    _auth()
    _config(monkeypatch)
    ig.clear_connection("dev-user")
    _mock_client(monkeypatch, long_lived_ok)
    auth_r = client.get("/api/instagram/auth-url")
    from urllib.parse import parse_qs, urlparse

    state = parse_qs(urlparse(auth_r.json()["url"]).query)["state"][0]
    r = client.get("/api/instagram/callback", params={"code": "abc", "state": state})
    assert r.status_code == 200, r.text
    return r.json()


def test_callback_intercambia_code_y_guarda_long_lived(monkeypatch):
    body = _do_callback(monkeypatch)
    assert body["estado"] == "conectado"
    assert body["can_publish"] is True
    conn = ig.get_connection("dev-user")
    assert conn is not None
    assert conn.access_token == "long-1"  # short → long-lived
    assert conn.expires_in_s == 5184000
    assert "instagram_business_content_publish" in conn.scopes

    # El módulo jamás define helpers de insights.
    assert not hasattr(ig, "fetch_insights")

    r = client.get("/api/instagram/status")
    assert r.json() == {"estado": "conectado", "username": "cafecito",
                        "followers_count": None, "media_count": None, "can_publish": True}


def test_callback_sigue_con_short_si_falla_long_lived(monkeypatch):
    _do_callback(monkeypatch, long_lived_ok=False)
    conn = ig.get_connection("dev-user")
    assert conn is not None
    assert conn.access_token == "short-1"
    assert conn.expires_in_s == 3600


def test_profile_conectado_devuelve_counts(monkeypatch):
    _do_callback(monkeypatch)
    r = client.get("/api/instagram/profile")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "cafecito"
    assert body["followers_count"] == 120
    assert body["media_count"] == 34


def test_validate_publish_input():
    ok_url, ok_cap = ig.validate_publish_input("https://cdn.x/f.jpg", "Hola")
    assert ok_url == "https://cdn.x/f.jpg" and ok_cap == "Hola"
    try:
        ig.validate_publish_input("not-a-url", "x")
    except ValueError:
        pass
    else:
        raise AssertionError("URL inválida aceptada")
    try:
        ig.validate_publish_input("https://cdn.x/f.jpg", "x" * 2201)
    except ValueError:
        pass
    else:
        raise AssertionError("Caption largo aceptado")


def test_encrypt_roundtrip_y_sin_key():
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    enc = ig.encrypt_token("tok-secreto", key)
    assert enc != "tok-secreto"
    assert ig.decrypt_token(enc, key) == "tok-secreto"
    try:
        ig.encrypt_token("x", "")
    except ValueError:
        pass
    else:
        raise AssertionError("Sin key debería fallar")


def test_disconnect_limpia_estado(monkeypatch):
    _auth()
    _config(monkeypatch)
    ig.save_connection("dev-user", "tok-x", "cafecito")
    r = client.delete("/api/instagram/disconnect")
    assert r.status_code == 200
    assert r.json()["estado"] == "desconectado"
    assert client.get("/api/instagram/status").json()["estado"] == "desconectado"
