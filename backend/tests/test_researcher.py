"""Tests del Researcher ramificado (local/online/mixto). Cero red real."""

import httpx
import pytest

from agents.researcher import haversine_m, researcher_node
from tools import places
from tools import tavily as tavily_mod

ANCHOR = {
    "id": "anchor1",
    "displayName": {"text": "Café Martínez"},
    "formattedAddress": "Av. Falsa 123, Palermo",
    "location": {"latitude": -34.58, "longitude": -58.43},
}
NEAR = {
    "id": "p-near",
    "displayName": {"text": "Café Cercano"},
    "rating": 4.5,
    "userRatingCount": 300,
    "formattedAddress": "Calle 1",
    "location": {"latitude": -34.581, "longitude": -58.431},
}
FAR = {
    "id": "p-far",
    "displayName": {"text": "Café Lejano"},
    "rating": 4.0,
    "userRatingCount": 100,
    "formattedAddress": "Calle 2",
    "location": {"latitude": -34.59, "longitude": -58.45},
}

TAVILY_PAYLOAD = {
    "results": [
        {
            "url": "https://tienda.example/cafe",
            "title": "Tienda Example",
            "content": "Café de especialidad online con envío gratis desde $20000.",
            "published_date": "2026-08-01",
        }
    ]
}


def _details_payload(pid):
    return {
        "id": pid,
        "websiteUri": f"https://{pid}.example",
        "regularOpeningHours": {"weekdayDescriptions": ["lunes: 8–20"]},
        "photos": [{"name": f"{pid}/photo1"}],
        "reviews": [
            {
                "text": {"text": f"Muy bueno {pid}, atención excelente"},
                "authorAttribution": {"displayName": "Ana"},
                "rating": 5,
                "publishTime": "2026-09-01T12:00:00Z",
            }
        ],
    }


def _make_handler(anchor_places=None, tavily_status=200):
    anchor_payload = [ANCHOR] if anchor_places is None else anchor_places

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "places:searchText" in url:
            body = request.read().decode()
            # Ancla: "{nombre}, {zona}" — competidores: "{tipo} en {zona}".
            if " en " not in body:
                return httpx.Response(200, json={"places": anchor_payload})
            return httpx.Response(200, json={"places": [ANCHOR, NEAR, FAR]})
        if "/places/" in url:
            pid = url.rstrip("/").split("/")[-1]
            return httpx.Response(200, json=_details_payload(pid))
        if "api.tavily.com" in url:
            return httpx.Response(tavily_status, json=TAVILY_PAYLOAD)
        raise AssertionError(f"URL inesperada: {url}")

    return handler


def _mock_net(monkeypatch, tmp_path, handler, google_key="k", tavily_key=""):
    monkeypatch.setattr(places.settings, "google_places_api_key", google_key)
    monkeypatch.setattr(tavily_mod.settings, "tavily_api_key", tavily_key)
    monkeypatch.setattr(places, "default_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)
    mock = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: real_client(transport=mock))


def _state(channel="local"):
    return {
        "business_name": "Café Martínez",
        "business_type": "café de especialidad",
        "zone": "Palermo",
        "sales_channel": channel,
    }


def test_local_excluye_ancla_y_ordena_por_distancia(monkeypatch, tmp_path):
    _mock_net(monkeypatch, tmp_path, _make_handler())
    out = researcher_node(_state("local"))
    ids = [c["place_id"] for c in out["competitors"]]
    assert "anchor1" not in ids
    assert ids == ["p-near", "p-far"]
    assert out["competitors"][0]["distance_m"] < out["competitors"][1]["distance_m"]
    assert out["anchor"]["place_id"] == "anchor1"
    assert out["reviews_by_place"]["p-near"]
    assert out["meta"]["stub"] is False
    assert out["trace"] == ["researcher"]


def test_haversine_sano():
    d = haversine_m(-34.58, -58.43, -34.581, -58.431)
    assert 100 < d < 200


def test_ancla_irresoluble_error_explicito(monkeypatch, tmp_path):
    _mock_net(monkeypatch, tmp_path, _make_handler(anchor_places=[]))
    with pytest.raises(places.AnchorNotFoundError, match="Verificá el nombre"):
        researcher_node(_state("local"))


def test_online_sin_tavily_key_error_claro(monkeypatch, tmp_path):
    _mock_net(monkeypatch, tmp_path, _make_handler(), tavily_key="")
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        researcher_node(_state("online"))


def test_online_tavily_primero(monkeypatch, tmp_path):
    _mock_net(monkeypatch, tmp_path, _make_handler(), google_key="", tavily_key="tk")
    out = researcher_node(_state("online"))
    assert out["competitors"], "online sin señales no sirve"
    assert all(c["source"] == "web" for c in out["competitors"])
    assert out["web_signals"][0]["url"].startswith("https://tienda.example")
    assert out["meta"]["stub"] is False


def test_mixto_fusiona_con_origen(monkeypatch, tmp_path):
    _mock_net(monkeypatch, tmp_path, _make_handler(), tavily_key="tk")
    out = researcher_node(_state("mixto"))
    sources = {c["source"] for c in out["competitors"]}
    assert sources == {"maps", "web"}
    assert out["anchor"]["place_id"] == "anchor1"


def test_falla_tavily_no_rompe_maps(monkeypatch, tmp_path):
    from config import settings

    monkeypatch.setattr(settings, "tavily_enabled", True)
    _mock_net(monkeypatch, tmp_path, _make_handler(tavily_status=500), tavily_key="tk")
    out = researcher_node(_state("local"))
    assert len(out["competitors"]) == 2
    assert any("tavily" in e for e in out["meta"]["research_errors"])


def test_endpoint_404_cuando_ancla_no_existe(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from config import settings
    from main import app

    monkeypatch.setattr(settings, "auth_disabled", True)
    _mock_net(monkeypatch, tmp_path, _make_handler(anchor_places=[]))
    r = TestClient(app).post(
        "/api/analyze",
        json={
            "business_name": "No Existe",
            "business_type": "café",
            "zone": "Palermo",
            "sales_channel": "local",
        },
    )
    assert r.status_code == 404
    assert "Verificá" in r.json()["detail"]
