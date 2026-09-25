"""Strategist: reglas determinísticas (sin LLM) que convierten clusters en gaps.

Reglas:
- Cluster con sentimiento < -0.2 y >= 2 menciones → oportunidad (dolor rival).
- Confianza alta si count >= 5, media si no.
- Sin clusters negativos → oportunidad de confianza baja (explorar).
"""

from __future__ import annotations

_NEGATIVE_THRESHOLD = -0.2
_MIN_COUNT = 2


def strategist_node(state: dict) -> dict:
    opportunities: list[dict] = []
    for cluster in state.get("clusters", []):
        if cluster["avg_sentiment"] < _NEGATIVE_THRESHOLD and cluster["count"] >= _MIN_COUNT:
            examples = "; ".join(cluster.get("example_texts", [])[:2])
            opportunities.append(
                {
                    "title": f"Oportunidad en '{cluster['topic']}'",
                    "evidence": (
                        f"{cluster['count']} menciones con sentimiento "
                        f"{cluster['avg_sentiment']:.2f}. Ej: {examples}"
                    ),
                    "confidence": "alta" if cluster["count"] >= 5 else "media",
                }
            )
    if not opportunities:
        opportunities.append(
            {
                "title": "Sin gaps claros en los datos actuales",
                "evidence": "Ningún cluster negativo con volumen suficiente.",
                "confidence": "baja",
            }
        )
    rank = {"alta": 0, "media": 1, "baja": 2}
    opportunities.sort(key=lambda o: rank[o["confidence"]])
    return {"opportunities": opportunities, "trace": ["strategist"]}
