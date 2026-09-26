"""Researcher: ancla el comercio específico y busca competidores según el canal.

- `local`: resuelve el ancla en Maps → competidores con locationBias (círculo)
  → excluye el propio comercio → enriquece con Details (reviews, horarios, fotos).
- `online`: Tavily primero (quién vende lo mismo online, precios, marketplaces,
  links sociales) + Places best-effort.
- `mixto`: ambas ramas, merge con tags de origen.

Sin API keys: fixtures (dev/CI gratis, marcado stub=True). Con keys, el ancla
irresoluble es un error explícito (AnchorNotFoundError), nunca fixtures.
"""

from __future__ import annotations

import math
from urllib.parse import urlparse

import httpx

from config import settings
from state import Competitor
from tools.places import fetch_place_details, resolve_anchor, search_competitors

_FIXTURE_REVIEWS: dict[str, list[str]] = {
    "p1": [
        "El café es riquísimo y la atención excelente, vuelvo siempre",
        "Lugar hermoso, merienda increíble y personal muy amable",
        "Todo delicioso, el mejor café de especialidad del barrio",
        "Excelente atención, rápido y muy recomendable",
        "Me encanta este lugar, el flat white es perfecto",
        "Buenísimo todo, lindo ambiente y precios razonables",
        "Espectacular la pastelería, fresca y deliciosa",
        "Atención genial, se nota que aman lo que hacen",
    ],
    "p2": [
        "Pésima atención, esperé 40 minutos y el café llegó frío",
        "Muy caro para lo que es, porciones chicas y mala onda",
        "Café quemado y amargo, una decepción total",
        "Lentísimo todo, nunca más vuelvo a este lugar",
        "La comida llegó fría y cruda, horrible experiencia",
        "Precios carísimos y calidad mala, no lo recomiendo",
    ],
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _fixtures() -> dict:
    competitors = [
        {
            "place_id": "p1",
            "name": "Café de Especialidad A",
            "rating": 4.6,
            "user_ratings_total": 842,
            "address": "Palermo Soho",
            "cached": True,
            "source": "maps",
        },
        {
            "place_id": "p2",
            "name": "Café B",
            "rating": 3.4,
            "user_ratings_total": 210,
            "address": "Palermo Hollywood",
            "cached": True,
            "source": "maps",
        },
    ]
    return {
        "competitors": competitors,
        "reviews_by_place": _FIXTURE_REVIEWS,
        "last_review_by_place": {},
        "anchor": None,
        "web_signals": [],
        "meta": {"stub": True},
        "trace": ["researcher"],
    }


def _enrich_with_details(comp: Competitor, errors: list[str]) -> tuple[list[str], str | None]:
    """Details de un competidor. Devuelve (review_texts, last_review_iso)."""
    try:
        details = fetch_place_details(comp.place_id)
    except (httpx.HTTPError, RuntimeError, OSError, ValueError) as exc:
        # Degrada: se queda con campos de Search.
        errors.append(f"{comp.place_id}: {exc}")
        return [], None
    comp.opening_hours = details["opening_hours"]
    comp.photos = details["photos"]
    comp.website = details["website"]
    comp.reviews_fetched = len(details["reviews"])
    texts = [r["text"] for r in details["reviews"]]
    last = max((r["published_at"] for r in details["reviews"] if r["published_at"]), default=None)
    return texts, last


def _maps_branch(business_type: str, zone: str, anchor, errors: list[str]) -> tuple[list[dict], dict, dict]:
    bias = None
    if anchor and anchor.latitude is not None and anchor.longitude is not None:
        bias = {
            "latitude": anchor.latitude,
            "longitude": anchor.longitude,
            "radius_m": settings.search_radius_m,
        }
    found = search_competitors(business_type, zone, location_bias=bias)
    competitors, reviews, last_by_place = [], {}, {}
    for comp in found:
        if anchor and comp.place_id == anchor.place_id:
            continue  # el propio comercio no es su competidor
        comp.source = "maps"
        if bias and comp.latitude is not None and comp.longitude is not None:
            comp.distance_m = round(
                haversine_m(bias["latitude"], bias["longitude"], comp.latitude, comp.longitude), 1
            )
        texts, last = _enrich_with_details(comp, errors)
        if texts:
            reviews[comp.place_id] = texts
            if last:
                last_by_place[comp.place_id] = last
        competitors.append(comp.model_dump())
    competitors.sort(key=lambda c: (c.get("distance_m") is None, c.get("distance_m") or 0))
    return competitors, reviews, last_by_place


def _online_queries(business_name: str, business_type: str, zone: str) -> list[str]:
    return [
        f"{business_type} {zone} comprar online",
        f"comprar {business_type} online precios",
        f"{business_name} {business_type} opiniones",
    ][: max(1, settings.tavily_max_queries)]


def _web_branch(business_name: str, business_type: str, zone: str, errors: list[str]) -> tuple[list[dict], dict, list[dict]]:
    from tools.tavily import search_web_signals

    signals: list[dict] = []
    for q in _online_queries(business_name, business_type, zone):
        try:
            signals.extend(search_web_signals(q))
        except (httpx.HTTPError, RuntimeError, OSError, ValueError) as exc:
            errors.append(f"tavily '{q}': {exc}")
    competitors, reviews, seen = [], {}, set()
    for s in signals:
        domain = urlparse(s["url"]).netloc.lower().removeprefix("www.")
        if not domain or domain in seen:
            continue
        seen.add(domain)
        if len(competitors) >= settings.max_competitors:
            break
        wid = f"web:{domain}"
        competitors.append(
            Competitor(
                place_id=wid,
                name=s["title"] or domain,
                address=s["url"],
                website=f"https://{domain}",
                source="web",
            ).model_dump()
        )
        if s["snippet"]:
            reviews[wid] = [s["snippet"]]
    return competitors, reviews, signals


def researcher_node(state: dict) -> dict:
    business_name = (state.get("business_name") or "").strip()
    business_type = (state.get("business_type") or "").strip()
    zone = (state.get("zone") or "").strip()
    channel = state.get("sales_channel") or "local"
    errors: list[str] = []

    if not settings.google_places_api_key and not settings.tavily_api_key:
        return _fixtures()

    anchor = None
    competitors: list[dict] = []
    reviews: dict[str, list[str]] = {}
    last_by_place: dict[str, str] = {}
    web_signals: list[dict] = []

    wants_maps = channel in ("local", "mixto")
    wants_web = channel in ("online", "mixto") or (channel == "local" and settings.tavily_enabled)

    if wants_maps:
        if not settings.google_places_api_key:
            errors.append("sin GOOGLE_PLACES_API_KEY: rama Maps omitida")
        else:
            anchor = resolve_anchor(business_name, zone)  # 404 explícito si no existe
            maps_comps, maps_reviews, maps_last = _maps_branch(business_type, zone, anchor, errors)
            competitors.extend(maps_comps)
            reviews.update(maps_reviews)
            last_by_place.update(maps_last)

    if wants_web:
        if not settings.tavily_api_key:
            msg = "sin TAVILY_API_KEY: rama web omitida"
            if channel == "online":
                raise RuntimeError(
                    "El canal online requiere TAVILY_API_KEY en backend/.env "
                    "(o usá sales_channel=local)."
                )
            errors.append(msg)
        else:
            web_comps, web_reviews, web_signals = _web_branch(business_name, business_type, zone, errors)
            have_ids = {c["place_id"] for c in competitors}
            for c in web_comps:
                if c["place_id"] not in have_ids:
                    competitors.append(c)
            reviews.update(web_reviews)

    return {
        "competitors": competitors[: settings.max_competitors],
        "reviews_by_place": reviews,
        "last_review_by_place": last_by_place,
        "anchor": anchor.model_dump() if anchor else None,
        "web_signals": web_signals,
        "meta": {"stub": False, "sales_channel": channel, "research_errors": errors},
        "trace": ["researcher"],
    }
