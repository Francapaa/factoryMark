"""CORS: el browser frena el POST en el preflight si el origen no está permitido.

Regresión real: con el frontend en http://127.0.0.1:3000 el preflight a
/api/businesses/resolve devolvía 400 "Disallowed CORS origin" y el form de
onboarding parecía no hacer nada (ni siquiera salía el POST en Network).
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _preflight(origin: str):
    return client.options(
        "/api/businesses/resolve",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


def test_preflight_localhost_ok():
    r = _preflight("http://localhost:3000")
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_preflight_127_ok():
    r = _preflight("http://127.0.0.1:3000")
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_preflight_origen_externo_rechazado():
    r = _preflight("https://evil.test")
    assert r.status_code == 400
