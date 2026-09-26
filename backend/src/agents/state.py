"""Estado compartido del grafo (contrato entre nodos)."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    business_name: str
    business_type: str
    zone: str
    sales_channel: str
    anchor: dict | None
    competitors: list[dict]
    reviews_by_place: dict[str, list[str]]
    last_review_by_place: dict[str, str]
    web_signals: list[dict]
    clusters: list[dict]
    scores: dict[str, float]
    opportunities: list[dict]
    draft_post: dict | None
    trace: Annotated[list[str], operator.add]
