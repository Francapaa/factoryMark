"""Tests de autenticación (Neon Auth, solo Google). Sin llamadas de red."""

import pytest
from fastapi.testclient import TestClient

import auth
from auth import CurrentUser, get_jwks_url, verify_neon_jwt
from config import settings
from main import app

client = TestClient(app)

PAYLOAD = {"business_type": "café", "zone": "Palermo Soho"}


@pytest.fixture(autouse=True)
def _clean_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", False)
    monkeypatch.setattr(settings, "neon_auth_base_url", "")
    monkeypatch.setattr(settings, "neon_auth_jwks_url", "")
    auth._jwks_clients.clear()


def test_analyze_sin_token_da_401():
    r = client.post("/api/analyze", json=PAYLOAD)
    assert r.status_code == 401
    assert "token" in r.json()["detail"].lower()


def test_approve_sin_token_da_401():
    r = client.post("/api/approve", json={"approved": True})
    assert r.status_code == 401


def test_token_malformado_da_401_sin_red(monkeypatch):
    # Token basura: PyJWKClient falla al decodificar antes de hacer red.
    monkeypatch.setattr(settings, "neon_auth_base_url", "https://auth.test.neon.tech")
    with pytest.raises(Exception) as exc:
        verify_neon_jwt("esto-no-es-un-jwt")
    assert getattr(exc.value, "status_code", None) == 401


def test_sin_base_url_da_503(monkeypatch):
    with pytest.raises(Exception) as exc:
        verify_neon_jwt("a.b.c")
    assert getattr(exc.value, "status_code", None) == 503


def test_auth_disabled_permite_pasar(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", True)
    r = client.post("/api/analyze", json=PAYLOAD)
    assert r.status_code == 200
    assert r.json()["meta"]["user_id"] == "dev-user"


def test_usuario_mockeado_llega_al_endpoint(monkeypatch):
    async def _fake_dep():
        return CurrentUser(id="u-123", email="a@b.com", name="A")

    # Override con dependencia sync/async indistinto para FastAPI
    from main import app as _app

    _app.dependency_overrides[auth.get_current_user] = _fake_dep
    try:
        r = client.post("/api/analyze", json=PAYLOAD)
        assert r.status_code == 200
        assert r.json()["meta"]["user_id"] == "u-123"
    finally:
        _app.dependency_overrides.clear()


def test_jwks_url_se_deriva_del_base(monkeypatch):
    monkeypatch.setattr(settings, "neon_auth_base_url", "https://auth.test.neon.tech/")
    monkeypatch.setattr(settings, "neon_auth_jwks_url", "")
    assert get_jwks_url() == "https://auth.test.neon.tech/.well-known/jwks.json"


def test_jwks_url_override(monkeypatch):
    monkeypatch.setattr(settings, "neon_auth_jwks_url", "https://otro/jwks.json")
    assert get_jwks_url() == "https://otro/jwks.json"
