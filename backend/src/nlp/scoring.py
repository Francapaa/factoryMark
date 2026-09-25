"""Scoring competitivo 0..1.

Decisiones de diseño (documentadas para la demo):
- rating pesa 50%: es la señal más comparable entre competidores.
- volumen (log) 25%: rendimientos decrecientes (100→1000 reviews no es 10x mejor).
- recencia 15%: última review <30 días = 1, decae lineal hasta 365 días = 0.
- actividad 10%: posteos/semana, saturado en 7 (1 por día).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime


def competitive_score(
    rating: float | None,
    total_reviews: int,
    last_review_iso: str | None,
    postings_per_week: float = 0.0,
) -> float:
    rating_part = (max(0.0, min(5.0, rating)) / 5.0) if rating else 0.0
    volume_part = min(1.0, math.log10(max(0, total_reviews) + 1) / 3.0)  # 1000 → 1.0
    recency_part = 0.0
    if last_review_iso:
        try:
            dt = datetime.fromisoformat(last_review_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            days = (datetime.now(UTC) - dt).days
            recency_part = max(0.0, 1.0 - max(0, days) / 365.0)
        except ValueError:
            recency_part = 0.0
    activity_part = max(0.0, min(1.0, postings_per_week / 7.0))
    return round(
        0.50 * rating_part + 0.25 * volume_part + 0.15 * recency_part + 0.10 * activity_part,
        4,
    )
