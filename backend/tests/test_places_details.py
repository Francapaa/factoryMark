"""Tests de Places Details, anchor y locationBias. Cero red real."""

import httpx
import pytest

from tools import places


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _search_payload(places_list):
    return {"places": places_list}


def test_bias_geografico_en_body(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read().decode()
        return httpx.Response(200, json=_search_payload([{"id": "p1"}]))

    places.search_competitors(
        "café",
        "Palermo",
        client=_client(handler),
        cache_dir=tmp_path,
        location_bias={"latitude": -34.58, "longitude": -58.43, "radius_m": 1000},
    )
    assert "locationBias" in seen["body"]
    assert "-34.58" in seen["body"]


def test_resolve_anchor_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    payload = _search_payload(
        [
            {
                "id": "anchor1",
                "displayName": {"text": "Café Martínez"},
                "formattedAddress": "Calle Falsa 123",
                "location": {"latitude": -34.58, "longitude": -58.43},
            }
        ]
    )
    anchor = places.resolve_anchor(
        "Café Martínez", "Palermo", client=_client(lambda r: httpx.Response(200, json=payload)), cache_dir=tmp_path
    )
    assert anchor.place_id == "anchor1"
    assert anchor.latitude == pytest.approx(-34.58)
    assert anchor.longitude == pytest.approx(-58.43)


def test_resolve_anchor_no_encontrado(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    with pytest.raises(places.AnchorNotFoundError, match="Verificá el nombre"):
        places.resolve_anchor(
            "No Existe",
            "Palermo",
            client=_client(lambda r: httpx.Response(200, json={"places": []})),
            cache_dir=tmp_path,
        )


def test_fetch_details_normaliza(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    monkeypatch.setattr(places.settings, "max_reviews_per_place", 20)
    payload = {
        "id": "p1",
        "websiteUri": "https://cafe.example",
        "regularOpeningHours": {"weekdayDescriptions": ["lunes: 8–20"]},
        "photos": [{"name": "photo/a"}, {"name": "photo/b"}],
        "reviews": [
            {
                "text": {"text": "Riquísimo"},
                "authorAttribution": {"displayName": "Ana"},
                "rating": 5,
                "publishTime": "2026-09-01T12:00:00Z",
            },
            {"text": {"text": "  "}, "rating": 1},  # vacía: se descarta
        ],
    }
    out = places.fetch_place_details(
        "p1", client=_client(lambda r: httpx.Response(200, json=payload)), cache_dir=tmp_path
    )
    assert out["website"] == "https://cafe.example"
    assert out["opening_hours"] == ["lunes: 8–20"]
    assert out["photos"] == ["photo/a", "photo/b"]
    assert len(out["reviews"]) == 1
    assert out["reviews"][0]["author"] == "Ana"


def test_fetch_details_cache_hit_sin_llamadas(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    payload = {"id": "p1", "reviews": []}
    client = _client(lambda r: httpx.Response(200, json=payload))
    places.fetch_place_details("p1", client=client, cache_dir=tmp_path)

    def boom(request: httpx.Request) -> httpx.Response:
        raise AssertionError("debió usar caché")

    out = places.fetch_place_details("p1", client=_client(boom), cache_dir=tmp_path)
    assert out["place_id"] == "p1"


def test_fetch_details_retry_ante_429(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "quota"})
        return httpx.Response(200, json={"id": "p1"})

    out = places.fetch_place_details("p1", client=_client(handler), cache_dir=tmp_path)
    assert calls["n"] == 2 and out["place_id"] == "p1"


def test_fetch_details_sin_key_error_claro(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "")
    with pytest.raises(RuntimeError, match="GOOGLE_PLACES_API_KEY"):
        places.fetch_place_details("p1", cache_dir=tmp_path)
