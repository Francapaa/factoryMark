"""Tests de autenticación (Neon Auth, solo Google). Sin llamadas de red."""

import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import auth
import db
from auth import CurrentUser, get_jwks_url, verify_neon_jwt
from config import settings
from main import app

client = TestClient(app)

PAYLOAD = {
    "business_name": "Café Ejemplo",
    "business_type": "café",
    "zone": "Palermo Soho",
    "sales_channel": "local",
}


def _saved(owner_id: str, **overrides) -> dict:
    saved = {
        "id": "b1",
        "owner_id": owner_id,
        "name": "Café Ejemplo",
        "business_type": "café",
        "sales_channel": "local",
        "zone": "Palermo Soho",
        "anchor_place_id": "anchor1",
        "anchor_snapshot": {},
        "brand_kit": None,
        "created_at": None,
        "updated_at": None,
    }
    saved.update(overrides)
    return saved


@pytest.fixture(autouse=True)
def _clean_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", False)
    monkeypatch.setattr(settings, "neon_auth_base_url", "")
    monkeypatch.setattr(settings, "neon_auth_jwks_url", "")
    auth._jwks_clients.clear()
    auth._jwks_json_cache.clear()


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
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
    r = client.post("/api/analyze", json=PAYLOAD)
    assert r.status_code == 200
    assert r.json()["meta"]["user_id"] == "dev-user"


def test_usuario_mockeado_llega_al_endpoint(monkeypatch):
    async def _fake_dep():
        return CurrentUser(id="u-123", email="a@b.com", name="A")

    # Override con dependencia sync/async indistinto para FastAPI
    from main import app as _app

    _app.dependency_overrides[auth.get_current_user] = _fake_dep
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
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


class _FakeJwksClient:
    """JWKS local: devuelve la pública Ed25519 sin red (el JWT es real, firmado acá)."""

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=self._public_key)


def _jwt_real(monkeypatch, iss, sub="user-1", exp_in=600, base_url=None, aud=None):
    import jwt as pyjwt
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(settings, "neon_auth_base_url", base_url or iss)
    monkeypatch.setitem(auth._jwks_clients, get_jwks_url(), _FakeJwksClient(private_key.public_key()))
    now = int(time.time())
    claims = {"iss": iss, "sub": sub, "exp": now + exp_in, "iat": now}
    if aud is not None:
        claims["aud"] = aud
    return pyjwt.encode(
        claims,
        private_key,
        algorithm="EdDSA",
    )


def test_jwt_real_pasa_el_gate_y_llega_al_endpoint(monkeypatch):
    iss = "https://auth.test.neon.tech"
    token = _jwt_real(monkeypatch, iss)
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["owner_id"] == "user-1"


def test_jwt_de_otro_emisor_da_401(monkeypatch):
    token = _jwt_real(
        monkeypatch, "https://otro-emisor.test", base_url="https://auth.test.neon.tech"
    )

    def _no_db(owner_id):
        raise AssertionError("el gate debe rechazar antes de tocar la DB")

    monkeypatch.setattr(db, "get_my_business", _no_db)
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token de otro emisor"


def test_jwt_expirado_da_401(monkeypatch):
    iss = "https://auth.test.neon.tech"
    token = _jwt_real(monkeypatch, iss, exp_in=-10)
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_opaco_corto_da_401_token_invalido(monkeypatch):
    # Regresión del bug real: el frontend mandaba el session token opaco
    # (~32 chars) en vez del JWT y el backend devolvía 401 mudo.
    monkeypatch.setattr(settings, "neon_auth_base_url", "https://auth.test.neon.tech")
    r = client.get(
        "/api/businesses/mine", headers={"Authorization": "Bearer abcdef1234567890abcdef1234567890"}
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Token inválido"


def test_jwt_neon_con_path_en_base_e_iss_origen_pasa(monkeypatch):
    # Bug real 2026-10-01: NEON_AUTH_BASE_URL incluye /neondb/auth pero Neon
    # emite iss/aud como origen. El gate debe aceptar el origen.
    origin = "https://ep-test.neonauth.aws.neon.tech"
    base = f"{origin}/neondb/auth"
    token = _jwt_real(monkeypatch, origin, base_url=base, aud=origin)
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["owner_id"] == "user-1"


def test_jwt_con_aud_valida_pasa(monkeypatch):
    # PyJWT rechaza el token si trae aud y no se pasa audience: el backend
    # valida aud manual contra el set permitido en vez de fallar con 401 mudo.
    iss = "https://auth.test.neon.tech"
    token = _jwt_real(monkeypatch, iss, aud=iss)
    monkeypatch.setattr(db, "get_my_business", lambda owner_id: _saved(owner_id))
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_jwt_con_aud_de_otro_emisor_da_401(monkeypatch):
    iss = "https://auth.test.neon.tech"
    token = _jwt_real(monkeypatch, iss, aud="https://otro-emisor.test")

    def _no_db(owner_id):
        raise AssertionError("el gate debe rechazar antes de tocar la DB")

    monkeypatch.setattr(db, "get_my_business", _no_db)
    r = client.get("/api/businesses/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token de otro emisor"
