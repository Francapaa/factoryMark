"""Onboarding del dueño: resolver el local, confirmar y guardar (requiere auth)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

import db
from auth import CurrentUser, get_current_user
from config import settings
from tools import places
from tools.places import AnchorNotFoundError

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

# Token opaco de Places (`places/<id>/photos/<ref>`). Nada de URLs arbitrarias.
_PHOTO_REF_RE = re.compile(r"^places/[^/]+/photos/[^/]+$")


class ResolveRequest(BaseModel):
    name: str = Field(min_length=1, examples=["Café Martínez"])
    zone: str = Field(min_length=1, examples=["Palermo Soho, Buenos Aires"])


class ResolveResponse(BaseModel):
    place_id: str
    name: str
    address: str = ""
    rating: float | None = None
    hours_summary: list[str] = []
    photo_ref: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    maps_url: str
    cached: bool = False


class SaveBusinessRequest(BaseModel):
    # Nombre canónico de Maps tal cual vino en resolve (el dueño no renombra).
    name: str = Field(min_length=1)
    business_type: str = ""
    sales_channel: Literal["local", "online", "mixto"] = "local"
    zone: str = Field(min_length=1)
    anchor_place_id: str = Field(min_length=1)
    anchor_snapshot: dict = Field(default_factory=dict)


class BusinessResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    business_type: str = ""
    sales_channel: str = "local"
    zone: str = ""
    anchor_place_id: str
    anchor_snapshot: dict = Field(default_factory=dict)
    brand_kit: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


def _db_unavailable(exc: RuntimeError) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


@router.post("/resolve", response_model=ResolveResponse)
def resolve_business(
    req: ResolveRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ResolveResponse:
    """Nombre + zona in → top-1 candidato anclado. 404 si no hay match, nunca inventa."""
    _ = user
    try:
        anchor = places.resolve_anchor(req.name.strip(), req.zone.strip())
    except AnchorNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "negocio_no_encontrado",
                "message": str(exc),
            },
        )
    except RuntimeError as exc:  # sin key u otro error explícito
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        details = places.fetch_place_details(anchor.place_id)
    except (httpx.HTTPError, RuntimeError, OSError, ValueError):
        details = {"opening_hours": [], "photos": [], "rating": None}
    photos = details.get("photos") or []
    hours = details.get("opening_hours") or []
    return ResolveResponse(
        place_id=anchor.place_id,
        name=anchor.name,
        address=anchor.address,
        rating=details.get("rating"),
        hours_summary=[str(h) for h in hours[:7]],
        photo_ref=photos[0] if photos else None,
        latitude=anchor.latitude,
        longitude=anchor.longitude,
        maps_url=f"https://www.google.com/maps/search/?api=1&query_place_id={anchor.place_id}",
    )


def fetch_photo_bytes(photo_ref: str) -> tuple[bytes, str]:
    """Baja la foto con la key server-side. Devuelve (bytes, content_type)."""
    resp = httpx.get(
        f"https://places.googleapis.com/v1/{photo_ref}/media",
        params={"maxHeightPx": 800},
        headers={"X-Goog-Api-Key": settings.google_places_api_key},
        timeout=20.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("content-type", "image/jpeg")


@router.get("/photo")
def business_photo(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    photo_ref: str = Query(min_length=1),
) -> Response:
    """Proxy de foto: el browser nunca ve la key. Solo tokens opacos, nada de URLs."""
    _ = user
    if "://" in photo_ref or ".." in photo_ref or not _PHOTO_REF_RE.match(photo_ref):
        raise HTTPException(status_code=400, detail="photo_ref inválido")
    if not settings.google_places_api_key:
        raise HTTPException(status_code=400, detail="Falta GOOGLE_PLACES_API_KEY en backend/.env")
    try:
        content, content_type = fetch_photo_bytes(photo_ref)
    except (httpx.HTTPError, RuntimeError, OSError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo cargar la foto: {exc}")
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.post("", response_model=BusinessResponse)
def save_business(
    req: SaveBusinessRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BusinessResponse:
    """Guarda el negocio confirmado (upsert: re-onboarding reemplaza la fila)."""
    snapshot = dict(req.anchor_snapshot or {})
    snapshot.setdefault("resolved_at", datetime.now(UTC).isoformat())
    try:
        saved = db.save_my_business(
            user.id,
            name=req.name.strip(),
            business_type=req.business_type.strip(),
            sales_channel=req.sales_channel,
            zone=req.zone.strip(),
            anchor_place_id=req.anchor_place_id.strip(),
            anchor_snapshot=snapshot,
        )
    except RuntimeError as exc:  # DATABASE_URL ausente
        raise _db_unavailable(exc)
    return BusinessResponse(**saved)


@router.get("/mine", response_model=BusinessResponse)
def my_business(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BusinessResponse:
    """Lee mi negocio o 404 `sin_negocio` (el frontend redirige a /onboarding)."""
    try:
        found = db.get_my_business(user.id)
    except RuntimeError as exc:  # DATABASE_URL ausente
        raise _db_unavailable(exc)
    if found is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "sin_negocio",
                "message": "Completá el onboarding para registrar tu local",
            },
        )
    return BusinessResponse(**found)
