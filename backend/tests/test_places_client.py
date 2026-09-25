"""Tests del cliente: dedup, límites, retry 429 y error sin key. Cero red real."""

import httpx
import pytest

from factorymark.tools import places


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_dedup_por_place_id(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    payload = {
        "places": [
            {"id": "dup", "displayName": {"text": "A"}},
            {"id": "dup", "displayName": {"text": "A bis"}},
            {"id": "ok", "displayName": {"text": "B"}},
        ]
    }
    res = places.search_competitors("bar", "Centro", client=_client(lambda r: httpx.Response(200, json=payload)), cache_dir=tmp_path)
    assert [c.place_id for c in res] == ["dup", "ok"]


def test_respeta_max_competitors(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    monkeypatch.setattr(places.settings, "max_competitors", 2)
    payload = {"places": [{"id": f"p{i}"} for i in range(10)]}
    res = places.search_competitors("bar", "Centro", client=_client(lambda r: httpx.Response(200, json=payload)), cache_dir=tmp_path)
    assert len(res) == 2


def test_retry_ante_429(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "k")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "quota"})
        return httpx.Response(200, json={"places": [{"id": "p1"}]})

    res = places.search_competitors("bar", "Centro", client=_client(handler), cache_dir=tmp_path)
    assert calls["n"] == 2 and [c.place_id for c in res] == ["p1"]


def test_sin_api_key_error_claro(monkeypatch, tmp_path):
    monkeypatch.setattr(places.settings, "google_places_api_key", "")
    with pytest.raises(RuntimeError, match="GOOGLE_PLACES_API_KEY"):
        places.search_competitors("bar", "Centro", cache_dir=tmp_path)
