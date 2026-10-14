"""Instagram-Login (v2): conexión + publicación + programación.

Flavor Instagram-Login contra `graph.instagram.com` (Business Login for
Instagram): no requiere Facebook Page. v2 pide
`instagram_business_basic` + `instagram_business_content_publish`.

Flujo de tokens (server-side, el secret nunca llega al browser):
code → short-lived (1h) → long-lived (60 días) → refresh (≥24h de vida).

Flujo de publicación (foto simple primero):
POST /me/media (image_url público + caption) → container_id
→ poll GET /{container}?fields=status_code hasta FINISHED
→ POST /me/media_publish (creation_id) → media_id.

La programación NO es nativa de la API (Instagram no acepta
`scheduled_for`): la cola vive en `app.publicaciones` (o memoria si no
hay DATABASE_URL) y un worker/cron publica lo vencido vía
`POST /api/instagram/scheduled/run-due`.

Insights: fuera de alcance en v2 (requiere otro permiso + App Review).
Este módulo no define helpers de insights a propósito.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_BASE = "https://graph.instagram.com"
V1_SCOPE = "instagram_business_basic"
PUBLISH_SCOPE = "instagram_business_content_publish"
# v2: login + publicación en un solo consentimiento (re-autoriza a quien
# conectó en v1; el `state` por usuario protege contra CSRF).
V2_SCOPES = (V1_SCOPE, PUBLISH_SCOPE)

# Caption máximo de Instagram para feed.
MAX_CAPTION_LENGTH = 2200
# Límite oficial (docs Content Publishing): 100 posts/24h móvil.
PUBLISH_LIMIT_PER_24H = 100
# Poll del container: fotos procesan rápido; videos pueden tardar.
POLL_MAX_ATTEMPTS = 5
POLL_INTERVAL_S = 3.0
# Refresh permitido solo con 24h+ de vida y token aún vigente.
REFRESH_MIN_AGE_S = 3600 * 24

TERMINAL_CONTAINER_STATUS = ("FINISHED", "PUBLISHED", "ERROR", "EXPIRED")


@dataclass
class InstagramConnection:
    user_id: str
    access_token: str
    username: str = ""
    obtained_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_in_s: int = 3600 * 24 * 60  # long-lived ≈ 60 días
    scopes: str = V1_SCOPE
    ig_user_id: str = ""


_store: dict[str, InstagramConnection] = {}
# States OAuth pendientes por usuario (CSRF). Se consumen en el callback.
_pending_states: dict[str, set[str]] = {}


def is_configured(client_id: str, redirect_uri: str) -> bool:
    return bool(client_id and redirect_uri)


def has_publish_scope(scopes: str) -> bool:
    return PUBLISH_SCOPE in (scopes or "")


def build_auth_url(
    client_id: str, redirect_uri: str, state: str, scopes: tuple[str, ...] = V2_SCOPES
) -> str:
    """URL de autorización OAuth (flavor Instagram-Login, scopes v2)."""
    qs = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{qs}"


def new_state() -> str:
    return secrets.token_urlsafe(24)


def remember_state(user_id: str, state: str) -> None:
    _pending_states.setdefault(user_id, set()).add(state)


def consume_state(user_id: str, state: str) -> bool:
    """True si el state era esperado (o si no había pendientes: dev/back-compat).

    Con pendientes sin matchear → False (posible CSRF, el callback debe 400).
    """
    pending = _pending_states.get(user_id)
    if not pending:
        return True
    if state in pending:
        pending.discard(state)
        return True
    return False


def _post_form(url: str, data: dict, client: httpx.Client | None) -> dict:
    own = client is None
    client = client or httpx.Client()
    try:
        resp = client.post(url, data=data, timeout=20.0)
        resp.raise_for_status()
        body = resp.json()
    finally:
        if own:
            client.close()
    if not isinstance(body, dict):
        raise TypeError(f"Respuesta inválida de {url}")
    return body


def _get_json(url: str, params: dict, client: httpx.Client | None) -> dict:
    own = client is None
    client = client or httpx.Client()
    try:
        resp = client.get(url, params=params, timeout=20.0)
        resp.raise_for_status()
        body = resp.json()
    finally:
        if own:
            client.close()
    if not isinstance(body, dict):
        raise TypeError(f"Respuesta inválida de {url}")
    return body


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    *,
    client: httpx.Client | None = None,
) -> dict:
    """Intercambia el code por short-lived token (server-side)."""
    body = _post_form(
        TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        client,
    )
    if not body.get("access_token"):
        raise RuntimeError("Instagram no devolvió access_token")
    return body


def extract_ig_user_id(token_body: dict) -> str:
    """user_id con forma corta o envuelto en data[0] (ambos vistos en Meta)."""
    uid = token_body.get("user_id")
    if uid:
        return str(uid)
    data = token_body.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return str(data[0].get("user_id") or "")
    return ""


def exchange_for_long_lived(
    short_token: str, client_secret: str, *, client: httpx.Client | None = None
) -> dict:
    """Short-lived (1h) → long-lived (60 días). Requiere app secret: server-side."""
    body = _get_json(
        f"{GRAPH_BASE}/access_token",
        {
            "grant_type": "ig_exchange_token",
            "client_secret": client_secret,
            "access_token": short_token,
        },
        client,
    )
    if not body.get("access_token"):
        raise RuntimeError("Instagram no devolvió long-lived token")
    return body


def refresh_long_lived(token: str, *, client: httpx.Client | None = None) -> dict:
    """Renueva un long-lived por otros 60 días (solo si tiene 24h+ y sigue vigente)."""
    body = _get_json(
        f"{GRAPH_BASE}/refresh_access_token",
        {"grant_type": "ig_refresh_token", "access_token": token},
        client,
    )
    if not body.get("access_token"):
        raise RuntimeError("Instagram no renovó el token")
    return body


def conn_age_s(conn: InstagramConnection) -> float:
    return (datetime.now(UTC) - conn.obtained_at).total_seconds()


def needs_refresh(conn: InstagramConnection) -> bool:
    """True si conviene refrescar: 24h+ de vida y aún no expiró."""
    age = conn_age_s(conn)
    return age >= REFRESH_MIN_AGE_S and age < conn.expires_in_s


def maybe_refresh(conn: InstagramConnection, *, client: httpx.Client | None = None) -> bool:
    """Best-effort: refresca y actualiza la conexión. Nunca rompe el flujo."""
    if not needs_refresh(conn):
        return False
    try:
        body = refresh_long_lived(conn.access_token, client=client)
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError):
        return False
    conn.access_token = str(body["access_token"])
    try:
        conn.expires_in_s = int(body.get("expires_in", conn.expires_in_s))
    except (TypeError, ValueError):
        pass
    conn.obtained_at = datetime.now(UTC)
    return True


def fetch_profile(access_token: str, *, client: httpx.Client | None = None) -> dict:
    """Lee solo el perfil profesional (username, counts). Nada de insights."""
    body = _get_json(
        f"{GRAPH_BASE}/me",
        {
            "fields": "id,user_name,username,followers_count,media_count",
            "access_token": access_token,
        },
        client,
    )
    return body


def validate_publish_input(image_url: str, caption: str) -> tuple[str, str]:
    """Valida entrada de publicación. Devuelve (image_url, caption) normalizados."""
    image_url = (image_url or "").strip()
    caption = (caption or "").strip()
    if not image_url or not image_url.startswith(("https://", "http://")):
        raise ValueError("image_url debe ser una URL pública http(s)")
    if len(caption) > MAX_CAPTION_LENGTH:
        raise ValueError(f"El texto supera el máximo de {MAX_CAPTION_LENGTH} caracteres")
    return image_url, caption


def create_photo_container(
    access_token: str,
    image_url: str,
    caption: str = "",
    *,
    client: httpx.Client | None = None,
) -> str:
    """Crea el container de foto. La imagen debe estar en servidor público (Meta la curlea)."""
    image_url, caption = validate_publish_input(image_url, caption)
    body = _post_form(
        f"{GRAPH_BASE}/me/media",
        {"access_token": access_token, "image_url": image_url, "caption": caption},
        client,
    )
    container_id = str(body.get("id") or "")
    if not container_id:
        raise RuntimeError("Instagram no devolvió container_id")
    return container_id


def get_container_status(
    container_id: str, access_token: str, *, client: httpx.Client | None = None
) -> str:
    """IN_PROGRESS | FINISHED | PUBLISHED | ERROR | EXPIRED."""
    body = _get_json(
        f"{GRAPH_BASE}/{container_id}",
        {"fields": "status_code", "access_token": access_token},
        client,
    )
    return str(body.get("status_code") or "IN_PROGRESS")


def publish_container(
    access_token: str, creation_id: str, *, client: httpx.Client | None = None
) -> str:
    """Publica un container listo. Devuelve el media_id."""
    if not creation_id:
        raise ValueError("Falta creation_id (container_id)")
    body = _post_form(
        f"{GRAPH_BASE}/me/media_publish",
        {"access_token": access_token, "creation_id": creation_id},
        client,
    )
    media_id = str(body.get("id") or "")
    if not media_id:
        raise RuntimeError("Instagram no devolvió media_id")
    return media_id


def get_publishing_limit(
    access_token: str, *, client: httpx.Client | None = None
) -> dict:
    """Uso actual de cuota (100 posts/24h móvil). Para respetar el rate limit."""
    return _get_json(
        f"{GRAPH_BASE}/me/content_publishing_limit",
        {"access_token": access_token},
        client,
    )


def publish_photo_now(
    access_token: str,
    image_url: str,
    caption: str = "",
    *,
    client: httpx.Client | None = None,
    sleep_s: float = POLL_INTERVAL_S,
    max_attempts: int = POLL_MAX_ATTEMPTS,
) -> dict:
    """Orquesta container → poll → publish. `sleep_s=0` en tests."""
    container_id = create_photo_container(access_token, image_url, caption, client=client)
    status = ""
    for _ in range(max_attempts):
        try:
            status = get_container_status(container_id, access_token, client=client)
        except (httpx.HTTPError, RuntimeError, TypeError, ValueError):
            status = "IN_PROGRESS"
        if status in ("FINISHED", "PUBLISHED"):
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"El container quedó en estado {status}")
        if sleep_s > 0:
            time.sleep(sleep_s)
    else:
        status = get_container_status(container_id, access_token, client=client)
    if status not in ("FINISHED", "PUBLISHED"):
        raise RuntimeError(
            f"La imagen sigue procesándose ({status}): el container vence en 24h, reintentá publicar"
        )
    media_id = publish_container(access_token, container_id, client=client)
    return {"container_id": container_id, "media_id": media_id}


def encrypt_token(plain: str, key: str) -> str:
    """Cifra el token con Fernet. Key: Fernet.generate_key() en TOKEN_ENCRYPTION_KEY."""
    from cryptography.fernet import Fernet, InvalidToken  # noqa: F401 (re-export check)

    if not key:
        raise ValueError("Falta TOKEN_ENCRYPTION_KEY en backend/.env")
    try:
        fernet = Fernet(key.encode())
    except ValueError as exc:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY inválida: generá una con Fernet.generate_key()"
        ) from exc
    return fernet.encrypt(plain.encode()).decode()


def decrypt_token(enc: str, key: str) -> str:
    from cryptography.fernet import Fernet

    if not key:
        raise ValueError("Falta TOKEN_ENCRYPTION_KEY en backend/.env")
    try:
        fernet = Fernet(key.encode())
    except ValueError as exc:
        raise ValueError("TOKEN_ENCRYPTION_KEY inválida") from exc
    return fernet.decrypt(enc.encode()).decode()


def save_connection(
    user_id: str,
    access_token: str,
    username: str = "",
    expires_in_s: int = 3600 * 24 * 60,
    scopes: str = V1_SCOPE,
    ig_user_id: str = "",
) -> InstagramConnection:
    conn = InstagramConnection(
        user_id=user_id,
        access_token=access_token,
        username=username,
        expires_in_s=expires_in_s,
        scopes=scopes,
        ig_user_id=ig_user_id,
    )
    _store[user_id] = conn
    return conn


def get_connection(user_id: str) -> InstagramConnection | None:
    return _store.get(user_id)


def clear_connection(user_id: str) -> None:
    _store.pop(user_id, None)
    _pending_states.pop(user_id, None)


def connection_state(conn: InstagramConnection | None) -> str:
    """conectado | expirado | desconectado. Nunca falla en silencio: expira explícito."""
    if conn is None:
        return "desconectado"
    if datetime.now(UTC) - conn.obtained_at > timedelta(seconds=conn.expires_in_s):
        return "expirado"
    return "conectado"
