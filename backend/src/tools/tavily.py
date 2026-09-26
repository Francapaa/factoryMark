"""Cliente de Tavily (web search) con cache en disco.

Rol: fuente primaria en modo online/mixto (quién vende lo mismo online,
precios, marketplaces, links a perfiles sociales), enrichment opcional
en modo local. Solo guarda URL + snippet + fecha: nunca métricas de
redes (eso es Fase 2 vía Apify, pago).

Diseño espejo de tools/places.py: cache JSON con TTL, retry exponencial
ante 429/5xx, tests con `httpx.MockTransport` (cero llamadas reales).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from config import settings
from tools.places import _is_fresh, _should_retry, default_cache_dir

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def tavily_cache_key(query: str, max_results: int) -> str:
    raw = f"{query.strip().lower()}|{max_results}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def _read_signals_cache(path: Path, ttl_hours: int) -> list[dict] | None:
    import json

    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        if _is_fresh(entry["saved_at"], ttl_hours) and isinstance(entry["payload"], list):
            return entry["payload"]
    except (OSError, ValueError, KeyError):
        pass
    return None


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _post_tavily(client: httpx.Client, body: dict) -> dict:
    resp = client.post(TAVILY_SEARCH_URL, json=body, timeout=20.0)
    resp.raise_for_status()
    return resp.json()


def search_web_signals(
    query: str,
    *,
    client: httpx.Client | None = None,
    cache_dir: Path | None = None,
) -> list[dict]:
    """Una query a Tavily. Devuelve señales {url,title,snippet,published_date,query}.

    Sin key → RuntimeError (el caller decide si Tavily es obligatorio u opcional
    según el canal). Cache hit → cero llamadas pagas.
    """
    import json
    from datetime import UTC, datetime

    api_key = settings.tavily_api_key
    if not api_key:
        raise RuntimeError("Falta TAVILY_API_KEY en backend/.env")

    max_results = max(1, min(settings.tavily_max_results, 10))
    cdir = cache_dir or default_cache_dir()
    cpath = cdir / f"tavily_{tavily_cache_key(query, max_results)}.json"

    hit = _read_signals_cache(cpath, settings.tavily_cache_ttl_hours)
    if hit is not None:
        return hit

    own_client = client is None
    client = client or httpx.Client()
    try:
        data = _post_tavily(
            client,
            {
                # Tavily autentica por body (api_key), no por header.
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
            },
        )
    finally:
        if own_client:
            client.close()

    signals = []
    for r in data.get("results", []) or []:
        if not isinstance(r, dict) or not r.get("url"):
            continue
        signals.append(
            {
                "url": r["url"],
                "title": r.get("title", ""),
                "snippet": (r.get("content", "") or "")[:500],
                "published_date": r.get("published_date", "") or "",
                "query": query,
            }
        )
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(
        json.dumps({"saved_at": datetime.now(UTC).isoformat(), "payload": signals}),
        encoding="utf-8",
    )
    return signals


__all__ = ["search_web_signals", "tavily_cache_key"]
