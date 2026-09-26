"""Orquestación multi-agente con LangGraph.

Flujo: researcher → analyst → strategist → creator → publisher.
Todo nodo es local (stubs + NLP propio): cero llamadas a APIs externas.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.analyst import analyst_node
from agents.creator import creator_node
from agents.publisher import publisher_node
from agents.researcher import researcher_node
from agents.state import AgentState
from agents.strategist import strategist_node


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("creator", creator_node)
    graph.add_node("publisher", publisher_node)
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "strategist")
    graph.add_edge("strategist", "creator")
    graph.add_edge("creator", "publisher")
    graph.add_edge("publisher", END)
    return graph.compile()


graph = build_graph()


def run_analysis(business_name: str, business_type: str, zone: str, sales_channel: str = "local") -> dict:
    result = graph.invoke(
        {
            "business_name": business_name,
            "business_type": business_type,
            "zone": zone,
            "sales_channel": sales_channel,
        }
    )
    meta = result.get("meta") or {}
    meta.setdefault("stub", True)
    meta["trace"] = result.get("trace", [])
    result["meta"] = meta
    return result
