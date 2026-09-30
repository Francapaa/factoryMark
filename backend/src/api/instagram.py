"""Endpoints de Instagram v1: conectar + leer perfil (requieren auth)."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import CurrentUser, get_current_user
from config import settings
from instagram import (
    build_auth_url,
    clear_connection,
    connection_state,
    exchange_code,
    fetch_profile,
    get_connection,
    is_configured,
    new_state,
    save_connection,
)

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


class AuthUrlResponse(BaseModel):
    url: str


class StatusResponse(BaseModel):
    estado: str  # conectado | expirado | desconectado
    username: str | None = None
    followers_count: int | None = None
    media_count: int | None = None


def _require_config() -> None:
    if not is_configured(settings.instagram_client_id, settings.instagram_redirect_uri):
        raise HTTPException(
            status_code=400,
            detail="Instagram no configurado: falta INSTAGRAM_CLIENT_ID / INSTAGRAM_REDIRECT_URI",
        )


@router.get("/auth-url", response_model=AuthUrlResponse)
def auth_url(user: Annotated[CurrentUser, Depends(get_current_user)]) -> AuthUrlResponse:
    _ = user
    _require_config()
    url = build_auth_url(
        settings.instagram_client_id, settings.instagram_redirect_uri, new_state()
    )
    return AuthUrlResponse(url=url)


@router.get("/callback", response_model=StatusResponse)
def callback(
    code: str,
    state: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> StatusResponse:
    _ = state
    _require_config()
    if not settings.instagram_client_secret:
        raise HTTPException(status_code=400, detail="Falta INSTAGRAM_CLIENT_SECRET")
    try:
        token_body = exchange_code(
            code,
            settings.instagram_client_id,
            settings.instagram_client_secret,
            settings.instagram_redirect_uri,
        )
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"No pudimos completar la conexión: {exc}")
    access_token = str(token_body.get("access_token", ""))
    username = ""
    try:
        profile = fetch_profile(access_token)
        username = str(profile.get("username") or profile.get("user_name") or "")
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError):
        username = ""
    save_connection(user.id, access_token, username)
    return StatusResponse(estado="conectado", username=username or None)


@router.get("/status", response_model=StatusResponse)
def status(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    conn = get_connection(user.id)
    estado = connection_state(conn)
    if estado == "desconectado":
        return StatusResponse(estado=estado)
    return StatusResponse(estado=estado, username=(conn.username or None) if conn else None)


@router.get("/profile", response_model=StatusResponse)
def profile(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    conn = get_connection(user.id)
    if connection_state(conn) != "conectado" or conn is None:
        raise HTTPException(status_code=409, detail="Instagram no conectado")
    try:
        body = fetch_profile(conn.access_token)
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"No pudimos leer el perfil: {exc}")
    username = str(body.get("username") or body.get("user_name") or conn.username or "")
    conn.username = username
    followers = body.get("followers_count")
    media = body.get("media_count")
    return StatusResponse(
        estado="conectado",
        username=username or None,
        followers_count=int(followers) if isinstance(followers, (int, float)) else None,
        media_count=int(media) if isinstance(media, (int, float)) else None,
    )


@router.delete("/disconnect", response_model=StatusResponse)
def disconnect(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    clear_connection(user.id)
    return StatusResponse(estado="desconectado")
