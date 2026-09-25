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


def test_flujo_completo_orden_y_salida(monkeypatch):
    _block_network(monkeypatch)
    result = run_analysis("café", "Palermo Soho")

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
    result = run_analysis("café", "Palermo Soho")
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
