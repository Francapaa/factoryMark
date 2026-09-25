"""Tests del cache en disco: hit fresco, miss y expiración por TTL."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from tools import places


def _mock_client(payload: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_cache_miss_llama_red_y_guarda(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "test-key")
    payload = {
        "places": [
            {
                "id": "p1",
                "displayName": {"text": "Café A"},
                "rating": 4.5,
                "userRatingCount": 120,
                "formattedAddress": "Calle 1",
            }
        ]
    }
    res = places.search_competitors("café", "Palermo", client=_mock_client(payload), cache_dir=tmp_path)
    assert len(res) == 1 and res[0].cached is False
    assert list(tmp_path.glob("*.json")) != []


def test_cache_hit_no_llama_red(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "test-key")
    cached = [{"id": "p9", "displayName": {"text": "Café Cache"}, "rating": 4.0}]
    key = places.cache_key("café", "Palermo", places.settings.places_language)
    (tmp_path / f"{key}.json").write_text(
        json.dumps({"saved_at": datetime.now(UTC).isoformat(), "payload": cached}),
        encoding="utf-8",
    )

    def boom(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no debería llamar a la red en cache hit")

    res = places.search_competitors(
        "café", "Palermo", client=httpx.Client(transport=httpx.MockTransport(boom)), cache_dir=tmp_path
    )
    assert len(res) == 1 and res[0].cached is True and res[0].name == "Café Cache"


def test_cache_expirado_vuelve_a_red(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "test-key")
    key = places.cache_key("café", "Palermo", places.settings.places_language)
    old = (datetime.now(UTC) - timedelta(hours=places.settings.places_cache_ttl_hours + 1)).isoformat()
    (tmp_path / f"{key}.json").write_text(
        json.dumps({"saved_at": old, "payload": [{"id": "viejo"}]}), encoding="utf-8"
    )
    payload = {"places": [{"id": "nuevo", "displayName": {"text": "Nuevo"}}]}
    res = places.search_competitors("café", "Palermo", client=_mock_client(payload), cache_dir=tmp_path)
    assert [c.place_id for c in res] == ["nuevo"]
    assert res[0].cached is False
