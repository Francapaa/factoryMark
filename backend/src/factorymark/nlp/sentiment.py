"""Sentiment ES baseline por lexicón + negación.

Wave 2: reemplazar `score_sentiment` por modelo transformers multilingüe
manteniendo rango -1..1.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime

_POSITIVE = {
    "rico", "rica", "excelente", "bueno", "buena", "buenísimo", "genial",
    "encanta", "encantó", "recomiendo", "recomendable", "increíble",
    "perfecto", "perfecta", "atención", "amable", "rápido", "rápida",
    "volvere", "volveré", "delicioso", "espectacular", "hermoso", "lindo",
}
_NEGATIVE = {
    "malo", "mala", "malísimo", "horrible", "pésimo", "pésima", "lento",
    "lenta", "caro", "cara", "carísimo", "sucio", "sucia", "frío", "fría",
    "crudo", "cruda", "quemado", "salado", "feo", "fea", "decepción",
    "nunca", "jamás", "asco", "rude", "mal",
}
_NEGATIONS = {"no", "ni", "nunca", "jamás", "tampoco", "sin"}

_WORD = re.compile(r"[a-záéíóúñü]+")


def score_sentiment(text: str) -> float:
    words = _WORD.findall(text.lower())
    if not words:
        return 0.0
    score = 0
    for i, w in enumerate(words):
        val = 0
        if w in _POSITIVE:
            val = 1
        elif w in _NEGATIVE:
            val = -1
        if val and any(prev in _NEGATIONS for prev in words[max(0, i - 3) : i]):
            val = -val
        score += val
    return max(-1.0, min(1.0, score / max(1, len(words) / 4)))


def trend_by_month(reviews: list[tuple[str, str]]) -> dict[str, float]:
    """{(iso_date, text)} → {YYYY-MM: sentimiento promedio}."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for iso_date, text in reviews:
        try:
            dt = datetime.fromisoformat(iso_date)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        buckets[dt.strftime("%Y-%m")].append(score_sentiment(text))
    return {m: sum(v) / len(v) for m, v in sorted(buckets.items())}
