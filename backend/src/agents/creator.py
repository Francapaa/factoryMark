"""Creator: borrador de marketing a partir de la top oportunidad (local, sin LLM).

Wave futura: generar el copy con LLM usando el brand kit del negocio,
manteniendo la firma `creator_node(state) -> dict`.
"""

from __future__ import annotations

from publisher import build_draft

_DEFAULT_BRAND = {"name": "Tu negocio", "tone": "cercano y barrial", "handle": ""}


def creator_node(state: dict) -> dict:
    opportunities = state.get("opportunities", [])
    title = opportunities[0]["title"] if opportunities else "novedades del barrio"
    draft = build_draft(title, _DEFAULT_BRAND)
    return {"draft_post": draft.model_dump(mode="json"), "trace": ["creator"]}
