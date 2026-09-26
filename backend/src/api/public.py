"""Endpoints públicos sin auth: estado del servicio."""

from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["public"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "places_configured": bool(settings.google_places_api_key),
        "tavily_configured": bool(settings.tavily_api_key),
        "tavily_enabled_local": settings.tavily_enabled,
        "auth_configured": bool(settings.neon_auth_base_url),
        "auth_disabled": settings.auth_disabled,
        "limits": {
            "max_competitors": settings.max_competitors,
            "max_reviews_per_place": settings.max_reviews_per_place,
            "search_radius_m": settings.search_radius_m,
        },
    }
