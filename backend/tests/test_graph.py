"""Workflow E2E: stub como smoke + pipeline real con HTTP borde simulado.

- test_stub_solo_smoke: sin keys, verifica contrato mínimo (no asserts de fixture exacta).
- test_pipeline_real_detecta_dolor_rival: con keys + MockTransport, reviews reales
  con quejas de precio -> oportunidad 'precios altos'. Mutación: si strategist
  deja de mapear precio, falla.
"""

import httpx
import pytest

from graph import run_analysis
from state import AnalyzeResponse


@pytest.fixture(autouse=True)
def _modo_aislado(monkeypatch, tmp_path):
    import tools.places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(places_mod, "default_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)
    yield


@pytest.fixture
def _stub_keys(monkeypatch):
    import tools.places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(places_mod.settings, "google_places_api_key", "")
    monkeypatch.setattr(tavily_mod.settings, "tavily_api_key", "")


def test_stub_solo_smoke_sin_keys(_stub_keys):
    result = run_analysis("Café Ejemplo", "café", "Palermo Soho", "local")
    assert result["trace"] == ["researcher", "analyst", "strategist", "creator", "publisher"]
    assert result["meta"]["stub"] is True
    assert result["draft_post"]["status"] == "draft"
    assert len(result["draft_post"]["copy_text"]) > 0


def test_pipeline_real_detecta_dolor_rival(monkeypatch):
    """E2E sin stub: Maps devuelve 2 reviews de precio alto -> oportunidad real."""
    import tools.places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(places_mod.settings, "google_places_api_key", "k")
    monkeypatch.setattr(tavily_mod.settings, "tavily_api_key", "")

    anchor = {
        "id": "anchor1", "displayName": {"text": "Café Ejemplo"},
        "formattedAddress": "Calle 1",
        "location": {"latitude": -34.58, "longitude": -58.43},
    }
    rival = {
        "id": "p-rival", "displayName": {"text": "Café Rival"},
        "rating": 3.0, "userRatingCount": 50, "formattedAddress": "Calle 2",
        "location": {"latitude": -34.581, "longitude": -58.431},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "places:searchText" in url:
            body = request.read().decode()
            if " en " not in body:
                return httpx.Response(200, json={"places": [anchor]})
            return httpx.Response(200, json={"places": [anchor, rival]})
        if "/places/" in url:
            return httpx.Response(200, json={
                "id": "p-rival",
                "reviews": [
                    {"text": {"text": "Carísimo todo, precios por las nubes"},
                     "authorAttribution": {"displayName": "A"}, "rating": 1,
                     "publishTime": "2026-09-01T12:00:00Z"},
                    {"text": {"text": "Muy caro para lo que dan, no vuelvo"},
                     "authorAttribution": {"displayName": "B"}, "rating": 2,
                     "publishTime": "2026-09-02T12:00:00Z"},
                ],
            })
        raise AssertionError(f"URL inesperada: {url}")

    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: real_client(transport=httpx.MockTransport(handler)))

    result = run_analysis("Café Ejemplo", "café", "Palermo", "local")
    assert result["meta"]["stub"] is False
    # El dolor viene de datos reales (cluster negativo o categoría precio):
    # la evidencia debe citar nuestras reviews, no fixtures.
    joined = " ".join(o["evidence"] + " " + o["title"] for o in result["opportunities"])
    assert "Carísimo" in joined or "caro" in joined.lower(), joined


def test_salida_compatible_con_contrato(_stub_keys):
    result = run_analysis("Café Ejemplo", "café", "Palermo Soho", "local")
    response = AnalyzeResponse(
        competitors=result["competitors"], clusters=result["clusters"],
        opportunities=result["opportunities"], draft_post=result["draft_post"],
        meta=result["meta"],
    )
    assert response.draft_post is not None
    assert response.draft_post.status == "draft"


@pytest.mark.parametrize("nodo", ["researcher", "analyst", "strategist", "creator", "publisher"])
def test_grafo_contiene_los_5_nodos(nodo):
    from graph import graph

    assert nodo in graph.nodes
