"""Cliente de Google Places API (New) con cache en disco.

Diseñado para NO quemar la cuota inicial ($20):
- Cache JSON por query con TTL de 7 días (ver `places_cache_ttl_hours`).
- Límites `max_competitors` / `language` desde settings.
- Retry exponencial ante 429/5xx (tenacity, max 3 intentos).
- Los tests usan `httpx.MockTransport`: cero llamadas reales.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from config import settings
from state import Anchor, Competitor

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
_SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.rating,"
    "places.userRatingCount,places.formattedAddress,places.location"
)
_DETAILS_FIELD_MASK = (
    "id,displayName,rating,userRatingCount,formattedAddress,websiteUri,"
    "regularOpeningHours,photos,reviews"
)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class AnchorNotFoundError(RuntimeError):
    """El comercio específico no se encontró en Maps: error explícito, no fixtures."""


def default_cache_dir() -> Path:
    # backend/src/tools/places.py -> parents[2] == backend/
    return Path(__file__).resolve().parents[2] / "data" / "cache"


def cache_key(business_type: str, zone: str, language: str) -> str:
    raw = f"{business_type.strip().lower()}|{zone.strip().lower()}|{language}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def _is_fresh(saved_at_iso: str, ttl_hours: int) -> bool:
    saved = datetime.fromisoformat(saved_at_iso)
    if saved.tzinfo is None:
        saved = saved.replace(tzinfo=UTC)
    return datetime.now(UTC) - saved < timedelta(hours=ttl_hours)


def _read_cache(path: Path, ttl_hours: int) -> list[dict] | None:
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        if _is_fresh(entry["saved_at"], ttl_hours) and isinstance(entry["payload"], list):
            return entry["payload"]
    except (OSError, ValueError, KeyError):
        pass
    return None


def _write_cache(path: Path, payload: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"saved_at": datetime.now(UTC).isoformat(), "payload": payload}),
        encoding="utf-8",
    )


def _should_retry(exc: BaseException) -> bool:
    return (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in _RETRYABLE_STATUS
    )


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _post_search(client: httpx.Client, api_key: str, body: dict) -> dict:
    resp = client.post(
        PLACES_SEARCH_URL,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": _SEARCH_FIELD_MASK,
        },
        json=body,
        timeout=20.0,
    )
    resp.raise_for_status()
    return resp.json()


def _to_competitors(raw_places: list[dict], cached: bool) -> list[Competitor]:
    seen: set[str] = set()
    out: list[Competitor] = []
    for p in raw_places:
        pid = str(p.get("id", ""))
        if not pid or pid in seen:
            continue
        seen.add(pid)
        name = p.get("displayName", {}).get("text", pid)
        loc = p.get("location", {}) or {}
        out.append(
            Competitor(
                place_id=pid,
                name=name,
                rating=p.get("rating"),
                user_ratings_total=int(p.get("userRatingCount", 0) or 0),
                address=p.get("formattedAddress", ""),
                cached=cached,
                latitude=loc.get("latitude"),
                longitude=loc.get("longitude"),
            )
        )
    return out


def search_competitors(
    business_type: str,
    zone: str,
    *,
    client: httpx.Client | None = None,
    cache_dir: Path | None = None,
    location_bias: dict | None = None,
) -> list[Competitor]:
    """Busca competidores. Cache hit → sin llamadas pagas (cached=True).

    `location_bias`: {"latitude": float, "longitude": float, "radius_m": int}
    para buscar por cercanía al comercio ancla (modo local).
    """
    api_key = settings.google_places_api_key
    if not api_key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY en backend/.env")

    language = settings.places_language
    bias_sig = ""
    if location_bias:
        bias_sig = (
            f"|{round(location_bias['latitude'], 4)}"
            f"|{round(location_bias['longitude'], 4)}"
            f"|{int(location_bias.get('radius_m', 0))}"
        )
    cdir = cache_dir or default_cache_dir()
    cpath = cdir / f"{cache_key(business_type + bias_sig, zone, language)}.json"

    hit = _read_cache(cpath, settings.places_cache_ttl_hours)
    if hit is not None:
        return _to_competitors(hit, cached=True)

    body: dict = {
        "textQuery": f"{business_type} en {zone}",
        "languageCode": language,
        "maxResultCount": max(1, min(settings.max_competitors, 20)),
    }
    if location_bias:
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": location_bias["latitude"],
                    "longitude": location_bias["longitude"],
                },
                "radius": float(location_bias.get("radius_m", settings.search_radius_m)),
            }
        }

    own_client = client is None
    client = client or httpx.Client()
    try:
        data = _post_search(client, api_key, body)
    finally:
        if own_client:
            client.close()

    raw = data.get("places", [])
    if not isinstance(raw, list):
        raw = []
    raw = raw[: settings.max_competitors]
    _write_cache(cpath, raw)
    return _to_competitors(raw, cached=False)


def resolve_anchor(
    business_name: str,
    zone: str,
    *,
    client: httpx.Client | None = None,
    cache_dir: Path | None = None,
) -> Anchor:
    """Resuelve el comercio específico a un ancla con coordenadas.

    Reusa Places Search (sin Geocoding API: otro SKU facturable innecesario).
    Lanza AnchorNotFoundError si no hay match: error explícito, nunca fixtures.
    """
    api_key = settings.google_places_api_key
    if not api_key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY en backend/.env")

    language = settings.places_language
    cdir = cache_dir or default_cache_dir()
    cpath = cdir / f"anchor_{cache_key(business_name, zone, language)}.json"

    hit = _read_cache(cpath, settings.places_cache_ttl_hours)
    raw_list = hit
    if raw_list is None:
        own_client = client is None
        client = client or httpx.Client()
        try:
            data = _post_search(
                client,
                api_key,
                {
                    "textQuery": f"{business_name}, {zone}",
                    "languageCode": language,
                    "maxResultCount": 1,
                },
            )
        finally:
            if own_client:
                client.close()
        raw_list = data.get("places", [])
        if not isinstance(raw_list, list):
            raw_list = []
        _write_cache(cpath, raw_list)

    if not raw_list:
        raise AnchorNotFoundError(
            f"No encontramos '{business_name}' en '{zone}' en Google Maps. "
            "Verificá el nombre del comercio."
        )
    top = raw_list[0]
    loc = top.get("location", {}) or {}
    return Anchor(
        place_id=str(top.get("id", "")),
        name=(top.get("displayName", {}) or {}).get("text", business_name),
        address=top.get("formattedAddress", ""),
        latitude=loc.get("latitude"),
        longitude=loc.get("longitude"),
    )


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _get_details(client: httpx.Client, api_key: str, place_id: str) -> dict:
    resp = client.get(
        PLACES_DETAILS_URL.format(place_id=place_id),
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": _DETAILS_FIELD_MASK,
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_place_details(
    place_id: str,
    *,
    client: httpx.Client | None = None,
    cache_dir: Path | None = None,
) -> dict:
    """Details por lugar: reviews, horarios, fotos, website. Cache 7 días.

    Devuelve dict normalizado:
    {"place_id", "reviews": [{"text","author","rating","published_at"}],
     "opening_hours": [...], "photos": [...], "website": str}
    """
    api_key = settings.google_places_api_key
    if not api_key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY en backend/.env")

    cdir = cache_dir or default_cache_dir()
    cpath = cdir / f"details_{place_id}.json"
    hit = _read_cache(cpath, settings.places_cache_ttl_hours)
    data = hit[0] if hit else None
    if not isinstance(data, dict):
        own_client = client is None
        client = client or httpx.Client()
        try:
            data = _get_details(client, api_key, place_id)
        finally:
            if own_client:
                client.close()
        if not isinstance(data, dict):
            data = {}
        _write_cache(cpath, [data])

    return _normalize_details(place_id, data)


def _normalize_details(place_id: str, data: dict) -> dict:
    reviews = []
    for r in data.get("reviews", []) or []:
        if not isinstance(r, dict):
            continue
        text = ((r.get("text") or {}).get("text", "") or "").strip()
        if not text:
            continue
        reviews.append(
            {
                "text": text,
                "author": ((r.get("authorAttribution") or {}).get("displayName", "") or ""),
                "rating": r.get("rating"),
                "published_at": r.get("publishTime", ""),
            }
        )
    hours = ((data.get("regularOpeningHours") or {}).get("weekdayDescriptions", []) or [])
    photos = [
        p.get("name", "")
        for p in (data.get("photos", []) or [])[:3]
        if isinstance(p, dict) and p.get("name")
    ]
    return {
        "place_id": place_id,
        "rating": data.get("rating"),
        "user_ratings_total": int(data.get("userRatingCount", 0) or 0),
        "reviews": reviews[: settings.max_reviews_per_place],
        "opening_hours": [str(h) for h in hours],
        "photos": photos,
        "website": data.get("websiteUri", "") or "",
    }
