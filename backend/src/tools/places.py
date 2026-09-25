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
from state import Competitor

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


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
            "X-Goog-FieldMask": "places.id,places.displayName,places.rating,"
            "places.userRatingCount,places.formattedAddress",
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
        out.append(
            Competitor(
                place_id=pid,
                name=name,
                rating=p.get("rating"),
                user_ratings_total=int(p.get("userRatingCount", 0) or 0),
                address=p.get("formattedAddress", ""),
                cached=cached,
            )
        )
    return out


def search_competitors(
    business_type: str,
    zone: str,
    *,
    client: httpx.Client | None = None,
    cache_dir: Path | None = None,
) -> list[Competitor]:
    """Busca competidores. Cache hit → sin llamadas pagas (cached=True)."""
    api_key = settings.google_places_api_key
    if not api_key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY en backend/.env")

    language = settings.places_language
    cdir = cache_dir or default_cache_dir()
    cpath = cdir / f"{cache_key(business_type, zone, language)}.json"

    hit = _read_cache(cpath, settings.places_cache_ttl_hours)
    if hit is not None:
        return _to_competitors(hit, cached=True)

    own_client = client is None
    client = client or httpx.Client()
    try:
        data = _post_search(
            client,
            api_key,
            {
                "textQuery": f"{business_type} en {zone}",
                "languageCode": language,
                "maxResultCount": max(1, min(settings.max_competitors, 20)),
            },
        )
    finally:
        if own_client:
            client.close()

    raw = data.get("places", [])
    if not isinstance(raw, list):
        raw = []
    raw = raw[: settings.max_competitors]
    _write_cache(cpath, raw)
    return _to_competitors(raw, cached=False)
