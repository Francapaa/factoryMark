"""Tests de Tavily: parseo, caché, retry y sin-key. Cero red real."""

import httpx
import pytest

from tools import tavily


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _payload():
    return {
        "results": [
            {
                "url": "https://tienda.example/producto",
                "title": "Tienda Example",
                "content": "Venden café de especialidad online con envío a todo el país. Precios accesibles.",
                "published_date": "2026-08-01",
            }
        ]
    }


def test_parsea_senales(monkeypatch, tmp_path):
    monkeypatch.setattr(tavily.settings, "tavily_api_key", "k")
    out = tavily.search_web_signals(
        "café online", client=_client(lambda r: httpx.Response(200, json=_payload())), cache_dir=tmp_path
    )
    assert len(out) == 1
    assert out[0]["url"] == "https://tienda.example/producto"
    assert "envío" in out[0]["snippet"]
    assert out[0]["query"] == "café online"


def test_cache_hit_sin_llamadas(monkeypatch, tmp_path):
    monkeypatch.setattr(tavily.settings, "tavily_api_key", "k")
    client = _client(lambda r: httpx.Response(200, json=_payload()))
    tavily.search_web_signals("café online", client=client, cache_dir=tmp_path)

    def boom(request: httpx.Request) -> httpx.Response:
        raise AssertionError("debió usar caché")

    out = tavily.search_web_signals("café online", client=_client(boom), cache_dir=tmp_path)
    assert len(out) == 1


def test_retry_ante_429(monkeypatch, tmp_path):
    monkeypatch.setattr(tavily.settings, "tavily_api_key", "k")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "quota"})
        return httpx.Response(200, json=_payload())

    out = tavily.search_web_signals("café online", client=_client(handler), cache_dir=tmp_path)
    assert calls["n"] == 2 and len(out) == 1


def test_sin_key_error_claro(monkeypatch, tmp_path):
    monkeypatch.setattr(tavily.settings, "tavily_api_key", "")
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        tavily.search_web_signals("café online", cache_dir=tmp_path)
