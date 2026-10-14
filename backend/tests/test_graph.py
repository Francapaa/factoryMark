"""Tests del workflow multi-agente. Prohíben red: todo debe ser local."""

import httpx
import httpx2
import pytest

from graph import run_analysis
from state import AnalyzeResponse


def _block_network(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("llamada de red prohibida en el workflow stub")

    monkeypatch.setattr(httpx.Client, "request", boom)
    monkeypatch.setattr(httpx2.Client, "request", boom)


@pytest.fixture(autouse=True)
def _modo_stub_aislado(monkeypatch, tmp_path):
    """Hermético: sin keys (fuerza fixtures, researcher.py:179) y sin caché
    real — o los datos del uso manual (backend/data/cache) rompen el stub."""
    import tools.places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(places_mod.settings, "google_places_api_key", "")
    monkeypatch.setattr(tavily_mod.settings, "tavily_api_key", "")
    monkeypatch.setattr(places_mod, "default_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)


def test_flujo_completo_orden_y_salida(monkeypatch):
    _block_network(monkeypatch)
    result = run_analysis("Café Ejemplo", "café", "Palermo Soho", "local")

    assert result["trace"] == ["researcher", "analyst", "strategist", "creator", "publisher"]
    assert len(result["competitors"]) == 2
    assert len(result["clusters"]) >= 1
    assert len(result["opportunities"]) >= 1

    opp = result["opportunities"][0]
    assert opp["confidence"] in ("alta", "media")
    assert "menciones" in opp["evidence"]

    draft = result["draft_post"]
    assert draft["status"] == "draft"
    assert len(draft["copy_text"]) > 0


def test_salida_compatible_con_contrato():
    result = run_analysis("Café Ejemplo", "café", "Palermo Soho", "local")
    response = AnalyzeResponse(
        competitors=result["competitors"],
        clusters=result["clusters"],
        opportunities=result["opportunities"],
        draft_post=result["draft_post"],
        meta=result["meta"],
    )
    assert response.draft_post is not None
    assert response.draft_post.status == "draft"


def test_sin_gaps_responde_baja_confianza():
    from agents.strategist import strategist_node

    out = strategist_node({"clusters": [{"topic": "todo bien", "count": 10, "avg_sentiment": 0.8}]})
    assert out["opportunities"][0]["confidence"] == "baja"
    assert out["trace"] == ["strategist"]


@pytest.mark.parametrize("nodo", ["researcher", "analyst", "strategist", "creator", "publisher"])
def test_grafo_contiene_los_5_nodos(nodo):
    from graph import graph

    assert nodo in graph.nodes
