"""Analyst: NLP propio (local, sin LLM ni red) sobre las reviews del Researcher."""

from __future__ import annotations

from nlp.cluster import cluster_reviews
from nlp.scoring import competitive_score


def analyst_node(state: dict) -> dict:
    reviews_by_place: dict[str, list[str]] = state.get("reviews_by_place", {})
    all_texts = [t for texts in reviews_by_place.values() for t in texts]
    clusters = [c.model_dump() for c in cluster_reviews(all_texts)]

    scores: dict[str, float] = {}
    for comp in state.get("competitors", []):
        scores[comp["place_id"]] = competitive_score(
            comp.get("rating"),
            comp.get("user_ratings_total", 0),
            None,
            0.0,
        )
    return {"clusters": clusters, "scores": scores, "trace": ["analyst"]}
