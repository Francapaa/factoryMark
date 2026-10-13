"""Strategist: reglas determinísticas (sin LLM) que convierten reviews en gaps.

Enfocado en dolor rival: los elogios no generan oportunidades, solo sirven
de contexto. Tres señales, en orden de peso:

1. Cluster negativo (sentimiento < -0.2, >= 2 menciones) → dolor temático.
2. Dolor por categoría ES+EN (espera, precio, servicio, calidad, limpieza)
   sobre reviews con señal negativa (sentiment < -0.2 o rating <= 2):
   >= 2 menciones de la misma categoría → oportunidad accionable.
3. Reviews de 1-2 estrellas sin categoría (>= 2) → dolor por rating.
4. Red de seguridad: si hay dolor pero ningún tema llegó a 2 menciones,
   cada reseña es su propia card (nunca se concatenan con ";").

Asignación única: cada review citada pertenece a una sola card (orden fijo:
cluster → primera categoría que matchee → rating → card individual).
Toda cita dice a qué negocio pertenece ("— Café B") y con qué estrellas.

- Confianza alta si count >= 5, media si no.
- Sin nada → oportunidad de confianza baja, honesta (no inventar).
- La evidencia cita textual (la API ya devuelve español con languageCode=es).
"""

from __future__ import annotations

import re

from nlp.sentiment import score_sentiment

_NEGATIVE_THRESHOLD = -0.2
_MIN_COUNT = 2
_LOW_RATING = 2  # estrellas: 1-2 es dolor explícito
_MAX_EXAMPLES = 3

# Patrones a palabra completa: un match parcial ("buscarlo" → precios,
# "carta" → precios) genera títulos sin sentido.
# El orden es el orden de asignación: la primera que matchee se queda la review.
_PAIN_CATEGORIES: dict[str, str] = {
    "esperas y demoras": r"\besper\w+|\blent[oa]s?|\blentísim[oa]s?|\blentisim[oa]s?|\b(tardó|tardan|tardaron|demor\w+)|\bnunca lleg\w*|\bno lleg\w+|\bslow\b|\bwait(?:ed|ing)?\b|\bmins?\b|\bhours?\b",
    "precios altos": r"\bcar[oa]s?|\bcarísim[oa]s?|\bcarisim[oa]s?|\bprecios?|\bexpensive\b|\boverpriced\b|\bcosts?\b|\bcostly\b|\$\s?\d",
    "mal servicio": r"\bservicio\b|\bservice\b|\bmozo\b|\bcamarer\w+|\bservers?\b|\brude\b|\blackluster\b|\bunimpressed\b|\bmala onda\b|\bmaleducad\w+|\bdesatent\w+|\batiend\w+|\bsirv\w+|\bsin lugar\b|\bno hay lugar\b|\bno hab[íi]a lugar\b|\bllen[oa]s?\b",
    "mala calidad de comida": r"\bfrí[oa]s?|\bfri[oa]s?|\bcold\b|\bcrud[oa]s?|\braw\b|\bquemad\w+|\bburnt\b|\bhorrible\b|\bhorrific\b|\bterrible\b|\bawful\b|\bgarbage\b|\bbeware\b|\bdecepci\w+|\bdisappoint\w+|\bpésim\w+|\bpesim\w+|\binedible\b|\btasteless\b",
    "higiene y limpieza": r"\bsuci[oa]s?|\bdirty\b|\blimpieza\b|\basco\b|\bdisgusting\b|\bhygiene\b",
}
_PAIN_RES = {name: re.compile(pat, re.IGNORECASE) for name, pat in _PAIN_CATEGORIES.items()}


def _confidence(count: int) -> str:
    return "alta" if count >= 5 else "media"


def _place_names(state: dict) -> dict[str, str]:
    """place_id → nombre del competidor (ya viaja en el state)."""
    names: dict[str, str] = {}
    for comp in state.get("competitors", []):
        pid = comp.get("place_id", "")
        if pid:
            names[pid] = comp.get("name") or pid
    return names


def _stars(rating) -> str:
    if isinstance(rating, bool):
        return ""
    if isinstance(rating, (int, float)):
        n = int(rating) if float(rating).is_integer() else rating
        return f" {n}★"
    return ""


def _cite(text: str, place_id: str, rating, names: dict[str, str]) -> str:
    """Cita completa con atribución: texto + negocio (+ estrellas)."""
    business = names.get(place_id, place_id)
    return f"{text.replace(chr(10), ' ')} — {business}{_stars(rating)}"


def _cluster_pains(state: dict, opportunities: list[dict]) -> set[str]:
    """Dolor temático por cluster. Devuelve los textos ya citados."""
    cited: set[str] = set()
    for cluster in state.get("clusters", []):
        if cluster["avg_sentiment"] < _NEGATIVE_THRESHOLD and cluster["count"] >= _MIN_COUNT:
            examples = [t.strip() for t in cluster.get("example_texts", []) if t.strip()]
            cited.update(examples)
            shown = "; ".join(e.replace("\n", " ") for e in examples[:_MAX_EXAMPLES])
            opportunities.append(
                {
                    "title": f"Oportunidad en '{cluster['topic']}'",
                    "evidence": (
                        f"{cluster['count']} menciones con sentimiento "
                        f"{cluster['avg_sentiment']:.2f}. Ej: {shown}"
                    ),
                    "confidence": _confidence(cluster["count"]),
                }
            )
    return cited


def _pain_reviews(state: dict, exclude: set[str]) -> list[dict]:
    """Reviews con señal negativa aún no citadas: {text, low, rating, place_id}."""
    reviews_by_place: dict[str, list[str]] = state.get("reviews_by_place", {})
    ratings_by_place: dict[str, list] = state.get("review_ratings", {})
    out: list[dict] = []
    for place_id, texts in reviews_by_place.items():
        ratings = ratings_by_place.get(place_id, [])
        for i, text in enumerate(texts):
            clean = (text or "").strip()
            if not clean or clean in exclude:
                continue
            rating = ratings[i] if i < len(ratings) else None
            low = isinstance(rating, (int, float)) and rating <= _LOW_RATING
            # Mismo umbral que clusters: un "-0.06" de un "nunca" perdido en un
            # elogio largo no es dolor (caso reseña de AGUSTINA).
            if not low and score_sentiment(clean) >= _NEGATIVE_THRESHOLD:
                continue
            out.append({"text": clean, "low": low, "rating": rating, "place_id": place_id})
    return out


def _category_pains(
    pains: list[dict], opportunities: list[dict], names: dict[str, str]
) -> list[dict]:
    """Asigna cada review a su primera categoría. Devuelve las no asignadas."""
    buckets: dict[str, list[dict]] = {name: [] for name in _PAIN_RES}
    unassigned: list[dict] = []
    for pain in pains:
        lowered = pain["text"].lower()
        for name, rx in _PAIN_RES.items():
            if rx.search(lowered):
                buckets[name].append(pain)
                break
        else:
            unassigned.append(pain)
    for name, hits in buckets.items():
        if len(hits) >= _MIN_COUNT:
            shown = "; ".join(
                _cite(p["text"], p["place_id"], p["rating"], names) for p in hits[:_MAX_EXAMPLES]
            )
            opportunities.append(
                {
                    "title": f"Dolor rival: {name} ({len(hits)} menciones)",
                    "evidence": (
                        f"{len(hits)} menciones con señal negativa sobre {name}. Ej: {shown}"
                    ),
                    "confidence": _confidence(len(hits)),
                }
            )
    return unassigned


def _low_rating_pains(
    leftovers: list[dict], opportunities: list[dict], names: dict[str, str]
) -> None:
    """Solo 1-2★ sin categoría: lo que no entró en ningún tema."""
    lows = [p for p in leftovers if p["low"]]
    if len(lows) >= _MIN_COUNT:
        shown = "; ".join(
            _cite(p["text"], p["place_id"], p["rating"], names) for p in lows[:_MAX_EXAMPLES]
        )
        opportunities.append(
            {
                "title": f"Dolor rival: {len(lows)} reviews de 1-2 estrellas",
                "evidence": (
                    f"{len(lows)} menciones con rating ≤ {_LOW_RATING} estrellas. Ej: {shown}"
                ),
                "confidence": _confidence(len(lows)),
            }
        )


def _general_pains(pains: list[dict], opportunities: list[dict], names: dict[str, str]) -> None:
    """Red de seguridad: si hay dolor pero ningún tema llegó a 2 menciones,
    cada reseña es su propia card con negocio y estrellas. Nunca se juntan."""
    if opportunities or len(pains) < _MIN_COUNT:
        return
    for pain in pains:
        business = names.get(pain["place_id"], pain["place_id"])
        opportunities.append(
            {
                "title": f"Reseña{_stars(pain['rating'])} · {business}",
                "evidence": pain["text"].replace("\n", " "),
                "confidence": "media",
            }
        )


def strategist_node(state: dict) -> dict:
    opportunities: list[dict] = []
    names = _place_names(state)
    cited = _cluster_pains(state, opportunities)
    pains = _pain_reviews(state, cited)
    leftovers = _category_pains(pains, opportunities, names)
    _low_rating_pains(leftovers, opportunities, names)
    _general_pains(pains, opportunities, names)
    # Seguridad: dos cards nunca comparten la misma evidencia textual.
    seen: set[str] = set()
    unique: list[dict] = []
    for opp in opportunities:
        if opp["evidence"] not in seen:
            seen.add(opp["evidence"])
            unique.append(opp)
    opportunities = unique
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
