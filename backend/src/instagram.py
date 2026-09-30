"""Instagram-Login (v1): conexión + lectura de perfil, sin publicar.

Flavor Instagram-Login contra `graph.instagram.com` (Business Login for
Instagram): no requiere Facebook Page. v1 pide solo
`instagram_business_basic`; el permiso de publicación
(`instagram_business_content_publish`) llega con el milestone de publish,
tras la aprobación de App Review.

Tokens: se guardan en memoria por usuario en esta fase. La persistencia
cifrada por negocio (`TOKEN_ENCRYPTION_KEY` + tabla de negocios) entra con
el endpoint `GET /api/businesses/mine` del agente de onboarding.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_BASE = "https://graph.instagram.com"
V1_SCOPE = "instagram_business_basic"

# La UI jamás debe disparar publicación en v1: no existen helpers para
# container/publish/insights en este módulo a propósito.
_FORBIDDEN_PATHS = ("media", "media_publish", "insights", "content_publishing")


@dataclass
class InstagramConnection:
    user_id: str
    access_token: str
    username: str = ""
    obtained_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_in_s: int = 3600 * 24 * 60  # long-lived ≈ 60 días


_store: dict[str, InstagramConnection] = {}


def is_configured(client_id: str, redirect_uri: str) -> bool:
    return bool(client_id and redirect_uri)


def build_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    """URL de autorización OAuth (flavor Instagram-Login, scope v1)."""
    qs = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": V1_SCOPE,
            "response_type": "code",
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{qs}"


def new_state() -> str:
    return secrets.token_urlsafe(24)


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    *,
    client: httpx.Client | None = None,
) -> dict:
    """Intercambia el code por access_token (server-side). Solo token, nunca publish."""
    own = client is None
    client = client or httpx.Client()
    try:
        resp = client.post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        body = resp.json()
    finally:
        if own:
            client.close()
    if not isinstance(body, dict) or not body.get("access_token"):
        raise RuntimeError("Instagram no devolvió access_token")
    return body


def fetch_profile(access_token: str, *, client: httpx.Client | None = None) -> dict:
    """Lee solo el perfil profesional (username, counts). Nada de insights."""
    own = client is None
    client = client or httpx.Client()
    try:
        resp = client.get(
            f"{GRAPH_BASE}/me",
            params={"fields": "user_name,username,followers_count,media_count", "access_token": access_token},
            timeout=20.0,
        )
        resp.raise_for_status()
        body = resp.json()
    finally:
        if own:
            client.close()
    if not isinstance(body, dict):
        raise TypeError("Respuesta de perfil inválida")
    return body


def save_connection(user_id: str, access_token: str, username: str = "", expires_in_s: int = 3600 * 24 * 60) -> InstagramConnection:
    conn = InstagramConnection(
        user_id=user_id, access_token=access_token, username=username, expires_in_s=expires_in_s
    )
    _store[user_id] = conn
    return conn


def get_connection(user_id: str) -> InstagramConnection | None:
    return _store.get(user_id)


def clear_connection(user_id: str) -> None:
    _store.pop(user_id, None)


def connection_state(conn: InstagramConnection | None) -> str:
    """valid | expirado | desconectado. Nunca falla en silencio: expira explícito."""
    if conn is None:
        return "desconectado"
    if datetime.now(UTC) - conn.obtained_at > timedelta(seconds=conn.expires_in_s):
        return "expirado"
    return "conectado"
