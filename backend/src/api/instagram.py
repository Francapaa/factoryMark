"""Endpoints de Instagram v2: conectar + publicar + programadas (requieren auth).

Ruta Instagram-Login (`graph.instagram.com`, sin Facebook Page).
La programación es cola propia: la API no tiene `scheduled_for` nativo.
Sin DATABASE_URL todo vive en memoria (dev/tests); con DB, el token va
cifrado (Fernet) y las programadas persisten en `app.publicaciones`.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import db
import instagram as ig
from auth import CurrentUser, get_current_user
from config import settings

logger = logging.getLogger("instagram_api")

router = APIRouter(prefix="/api/instagram", tags=["instagram"])

# Programadas: pasado (con 60s de tolerancia) y tope de 90 días.
SCHEDULE_PAST_TOLERANCE_S = 60
SCHEDULE_MAX_DAYS = 90


class AuthUrlResponse(BaseModel):
    url: str


class StatusResponse(BaseModel):
    estado: str  # conectado | expirado | desconectado
    username: str | None = None
    followers_count: int | None = None
    media_count: int | None = None
    can_publish: bool = False


class PublishRequest(BaseModel):
    image_url: str = Field(min_length=1, examples=["https://cdn.mi-local.com/post.jpg"])
    caption: str = ""


class PublishResponse(BaseModel):
    estado: str
    media_id: str
    container_id: str


class ScheduledCreate(BaseModel):
    image_url: str = Field(min_length=1)
    caption: str = ""
    copy_text: str = ""
    hashtags: list[str] = Field(default_factory=list)
    programada_para: datetime


class ScheduledPost(BaseModel):
    id: str
    estado: str
    image_url: str = ""
    caption: str = ""
    copy_text: str = ""
    hashtags: list[str] = Field(default_factory=list)
    programada_para: str | None = None
    container_id: str | None = None
    external_id: str | None = None
    error: str | None = None
    created_at: str | None = None
    published_at: str | None = None


class RunDueResponse(BaseModel):
    revisados: int
    publicados: int
    errores: list[dict] = Field(default_factory=list)


# Fallback en memoria (sin DATABASE_URL): mismo formato que las filas de DB.
_mem_posts: dict[str, dict[str, dict[str, Any]]] = {}


def _require_config() -> None:
    if not ig.is_configured(settings.instagram_client_id, settings.instagram_redirect_uri):
        raise HTTPException(
            status_code=400,
            detail="Instagram no configurado: falta INSTAGRAM_CLIENT_ID / INSTAGRAM_REDIRECT_URI",
        )


def _db_on() -> bool:
    return db.is_db_configured()


def _persist_conn(
    user_id: str,
    *,
    access_token: str,
    username: str,
    scopes: str,
    expires_in_s: int,
    ig_user_id: str,
) -> None:
    """Guarda en memoria siempre; en DB cifrada si hay DATABASE_URL."""
    ig.save_connection(
        user_id, access_token, username,
        expires_in_s=expires_in_s, scopes=scopes, ig_user_id=ig_user_id,
    )
    if not _db_on():
        return
    try:
        enc = ig.encrypt_token(access_token, settings.token_encryption_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        db.save_instagram_connection(
            user_id,
            ig_user_id=ig_user_id,
            username=username,
            access_token_enc=enc,
            scopes=scopes,
            expires_in_s=expires_in_s,
        )
    except Exception as exc:  # noqa: BLE001 - DB caída: la memoria sostiene la sesión
        raise HTTPException(status_code=503, detail=f"No pudimos guardar la conexión: {exc}")


def _load_conn(user_id: str) -> ig.InstagramConnection | None:
    """Lee DB cifrada si hay, si no memoria. Refresca best-effort si toca."""
    if not _db_on():
        return ig.get_connection(user_id)
    try:
        row = db.get_instagram_connection(user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"No pudimos leer la conexión: {exc}")
    if row is None:
        return ig.get_connection(user_id)
    try:
        token = ig.decrypt_token(row["access_token_enc"], settings.token_encryption_key)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    obtained = datetime.now(UTC)
    if row.get("obtained_at"):
        try:
            obtained = datetime.fromisoformat(row["obtained_at"])
        except ValueError:
            pass
    conn = ig.InstagramConnection(
        user_id=user_id,
        access_token=token,
        username=row.get("username") or "",
        obtained_at=obtained,
        expires_in_s=row.get("expires_in_s") or 0,
        scopes=row.get("scopes") or "",
        ig_user_id=row.get("ig_user_id") or "",
    )
    if ig.maybe_refresh(conn):
        _persist_conn(
            user_id,
            access_token=conn.access_token,
            username=conn.username,
            scopes=conn.scopes,
            expires_in_s=conn.expires_in_s,
            ig_user_id=conn.ig_user_id,
        )
    else:
        ig.save_connection(
            user_id, conn.access_token, conn.username,
            expires_in_s=conn.expires_in_s, scopes=conn.scopes, ig_user_id=conn.ig_user_id,
        )
        # Sincroniza la fecha base en memoria (la DB manda).
        mem = ig.get_connection(user_id)
        if mem is not None:
            mem.obtained_at = conn.obtained_at
    return conn


def _clear_conn(user_id: str) -> None:
    ig.clear_connection(user_id)
    if _db_on():
        try:
            db.clear_instagram_connection(user_id)
        except Exception as exc:  # noqa: BLE001 - desconectar nunca debe fallar
            logger.warning("No se pudo limpiar conexión IG en DB: %s", exc)


def _require_publisher(user_id: str) -> ig.InstagramConnection:
    """Conexión vigente + permiso de publicación, o error accionable."""
    conn = _load_conn(user_id)
    estado = ig.connection_state(conn)
    if estado != "conectado" or conn is None:
        raise HTTPException(
            status_code=409,
            detail="Instagram no conectado: conectá tu cuenta profesional primero",
        )
    if not ig.has_publish_scope(conn.scopes):
        raise HTTPException(
            status_code=409,
            detail="Falta el permiso de publicación: reconectá Instagram para otorgarlo",
        )
    return conn


def _validate_schedule(programada_para: datetime) -> datetime:
    when = programada_para
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    if when < now - timedelta(seconds=SCHEDULE_PAST_TOLERANCE_S):
        raise HTTPException(status_code=400, detail="La fecha programada debe estar en el futuro")
    if when > now + timedelta(days=SCHEDULE_MAX_DAYS):
        raise HTTPException(
            status_code=400, detail=f"Solo se puede programar hasta {SCHEDULE_MAX_DAYS} días"
        )
    return when


def _to_scheduled(row: dict[str, Any]) -> ScheduledPost:
    return ScheduledPost(
        id=str(row["id"]),
        estado=str(row.get("estado") or "programado"),
        image_url=str(row.get("image_url") or ""),
        caption=str(row.get("caption") or ""),
        copy_text=str(row.get("copy_text") or ""),
        hashtags=list(row.get("hashtags") or []),
        programada_para=row.get("programada_para"),
        container_id=row.get("container_id"),
        external_id=row.get("external_id"),
        error=row.get("error"),
        created_at=row.get("created_at"),
        published_at=row.get("published_at"),
    )


def _create_post(user_id: str, req: ScheduledCreate, when: datetime) -> ScheduledPost:
    if _db_on():
        try:
            row = db.create_scheduled_post(
                user_id,
                copy_text=req.copy_text.strip(),
                hashtags=req.hashtags,
                image_url=req.image_url.strip(),
                caption=req.caption.strip(),
                programada_para=when.isoformat(),
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos programar: {exc}")
        return _to_scheduled(row)
    import uuid as _uuid

    post_id = str(_uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    row: dict[str, Any] = {
        "id": post_id,
        "owner_id": user_id,
        "copy_text": req.copy_text.strip(),
        "hashtags": req.hashtags,
        "image_url": req.image_url.strip(),
        "caption": req.caption.strip(),
        "estado": "programado",
        "programada_para": when.isoformat(),
        "container_id": None,
        "external_id": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
        "published_at": None,
    }
    _mem_posts.setdefault(user_id, {})[post_id] = row
    return _to_scheduled(row)


def _list_posts(user_id: str) -> list[ScheduledPost]:
    if _db_on():
        try:
            rows = db.list_scheduled_posts(user_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos listar programadas: {exc}")
        return [_to_scheduled(r) for r in rows]
    rows = sorted(
        _mem_posts.get(user_id, {}).values(),
        key=lambda r: str(r.get("created_at") or ""),
        reverse=True,
    )
    return [_to_scheduled(r) for r in rows[:50]]


def _get_post(user_id: str, post_id: str) -> dict[str, Any] | None:
    if _db_on():
        try:
            return db.get_scheduled_post(user_id, post_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos leer la programada: {exc}")
    return _mem_posts.get(user_id, {}).get(post_id)


def _due_posts(user_id: str) -> list[dict[str, Any]]:
    if _db_on():
        try:
            return db.get_due_posts(user_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos leer vencidas: {exc}")
    now = datetime.now(UTC)
    due = []
    for row in _mem_posts.get(user_id, {}).values():
        if row.get("estado") != "programado" or not row.get("programada_para"):
            continue
        try:
            when = datetime.fromisoformat(str(row["programada_para"]))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        if when <= now:
            due.append(row)
    return sorted(due, key=lambda r: str(r.get("programada_para") or ""))


def _mark_published(user_id: str, post_id: str, container_id: str, external_id: str) -> None:
    if _db_on():
        try:
            db.mark_post_published(
                user_id, post_id, container_id=container_id, external_id=external_id
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos marcar publicado: {exc}")
        return
    row = _mem_posts.get(user_id, {}).get(post_id)
    if row is not None:
        row.update(
            {
                "estado": "publicado",
                "container_id": container_id,
                "external_id": external_id,
                "error": None,
                "published_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )


def _mark_error(user_id: str, post_id: str, error: str) -> None:
    if _db_on():
        try:
            db.mark_post_error(user_id, post_id, error=error)
        except Exception as exc:  # noqa: BLE001 - el error de publicación ya se reporta igual
            logger.warning("No se pudo marcar error en DB: %s", exc)
        return
    row = _mem_posts.get(user_id, {}).get(post_id)
    if row is not None:
        row.update(
            {"estado": "error", "error": error[:500], "updated_at": datetime.now(UTC).isoformat()}
        )


def _do_publish(conn: ig.InstagramConnection, image_url: str, caption: str) -> dict:
    try:
        image_url, caption = ig.validate_publish_input(image_url, caption)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        return ig.publish_photo_now(conn.access_token, image_url, caption)
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"No pudimos publicar: {exc}")


@router.get("/auth-url", response_model=AuthUrlResponse)
def auth_url(user: Annotated[CurrentUser, Depends(get_current_user)]) -> AuthUrlResponse:
    _require_config()
    state = ig.new_state()
    ig.remember_state(user.id, state)
    url = ig.build_auth_url(settings.instagram_client_id, settings.instagram_redirect_uri, state)
    return AuthUrlResponse(url=url)


@router.get("/callback", response_model=StatusResponse)
def callback(
    code: str,
    state: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> StatusResponse:
    _require_config()
    if not ig.consume_state(user.id, state):
        raise HTTPException(status_code=400, detail="State inválido: reintentá conectar")
    if not settings.instagram_client_secret:
        raise HTTPException(status_code=400, detail="Falta INSTAGRAM_CLIENT_SECRET")
    try:
        token_body = ig.exchange_code(
            code,
            settings.instagram_client_id,
            settings.instagram_client_secret,
            settings.instagram_redirect_uri,
        )
    except (httpx.HTTPError, RuntimeError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail=f"No pudimos completar la conexión: {exc}")
    short_token = str(token_body.get("access_token", ""))
    ig_user_id = ig.extract_ig_user_id(token_body)
    # Short (1h) → long-lived (60 días). Si falla, la sesión sigue con el corto.
    access_token = short_token
    expires_in_s = 3600
    granted_scopes = ",".join(ig.V2_SCOPES)
    try:
        long_body = ig.exchange_for_long_lived(short_token, settings.instagram_client_secret)
        access_token = str(long_body.get("access_token", short_token))
        expires_in_s = int(long_body.get("expires_in", 3600 * 24 * 60))
    except (httpx.HTTPError, RuntimeError, ValueError, TypeError):
        pass
    username = ""
    try:
        profile = ig.fetch_profile(access_token)
        username = str(profile.get("username") or profile.get("user_name") or "")
        ig_user_id = str(profile.get("id") or ig_user_id)
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError):
        username = ""
    _persist_conn(
        user.id,
        access_token=access_token,
        username=username,
        scopes=granted_scopes,
        expires_in_s=expires_in_s,
        ig_user_id=ig_user_id,
    )
    return StatusResponse(estado="conectado", username=username or None, can_publish=True)


@router.get("/status", response_model=StatusResponse)
def status(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    conn = _load_conn(user.id)
    estado = ig.connection_state(conn)
    if estado == "desconectado" or conn is None:
        return StatusResponse(estado="desconectado")
    if estado == "expirado":
        return StatusResponse(estado="expirado", username=(conn.username or None))
    return StatusResponse(
        estado="conectado",
        username=conn.username or None,
        can_publish=ig.has_publish_scope(conn.scopes),
    )


@router.get("/profile", response_model=StatusResponse)
def profile(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    conn = _load_conn(user.id)
    if ig.connection_state(conn) != "conectado" or conn is None:
        raise HTTPException(status_code=409, detail="Instagram no conectado")
    try:
        body = ig.fetch_profile(conn.access_token)
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
        can_publish=ig.has_publish_scope(conn.scopes),
    )


@router.delete("/disconnect", response_model=StatusResponse)
def disconnect(user: Annotated[CurrentUser, Depends(get_current_user)]) -> StatusResponse:
    _clear_conn(user.id)
    return StatusResponse(estado="desconectado")


@router.post("/publish", response_model=PublishResponse)
def publish_now(
    req: PublishRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PublishResponse:
    """Publica una foto ahora (2 pasos: container → publish). Requiere aprobación humana previa en la UI."""
    conn = _require_publisher(user.id)
    result = _do_publish(conn, req.image_url, req.caption)
    return PublishResponse(
        estado="publicado",
        media_id=result["media_id"],
        container_id=result["container_id"],
    )


@router.get("/limit")
def publishing_limit(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    """Cuota actual de publicación (100 posts/24h). Para no pasarse al programar."""
    conn = _require_publisher(user.id)
    try:
        return ig.get_publishing_limit(conn.access_token)
    except (httpx.HTTPError, RuntimeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"No pudimos leer la cuota: {exc}")


@router.post("/scheduled", response_model=ScheduledPost)
def create_scheduled(
    req: ScheduledCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ScheduledPost:
    """Programa una publicación futura. No llama a Meta: la cola es propia."""
    _require_publisher(user.id)
    try:
        ig.validate_publish_input(req.image_url, req.caption)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    when = _validate_schedule(req.programada_para)
    return _create_post(user.id, req, when)


@router.get("/scheduled", response_model=list[ScheduledPost])
def list_scheduled(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[ScheduledPost]:
    """Historial de programadas (nuevas primero): estados, recordatorios y reintentos."""
    _load_conn(user.id)  # 503/500 explícitos si la conexión está rota
    return _list_posts(user.id)


@router.delete("/scheduled/{post_id}", response_model=ScheduledPost)
def cancel_scheduled(
    post_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ScheduledPost:
    """Cancela una programada (se conserva como rechazada para auditoría)."""
    row = _get_post(user.id, post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Programada no encontrada")
    if str(row.get("estado")) != "programado":
        raise HTTPException(status_code=409, detail="Solo se puede cancelar una programada pendiente")
    if _db_on():
        try:
            ok = db.cancel_scheduled_post(user.id, post_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"No pudimos cancelar: {exc}")
        if not ok:
            raise HTTPException(status_code=409, detail="Ya no está pendiente")
        updated = _get_post(user.id, post_id)
        assert updated is not None
        return _to_scheduled(updated)
    row["estado"] = "rechazado"
    row["updated_at"] = datetime.now(UTC).isoformat()
    return _to_scheduled(row)


@router.post("/scheduled/{post_id}/publish-now", response_model=PublishResponse)
def publish_scheduled_now(
    post_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PublishResponse:
    """Adelanta una programada (o reintenta una con error): publica ahora."""
    conn = _require_publisher(user.id)
    row = _get_post(user.id, post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Programada no encontrada")
    if str(row.get("estado")) not in ("programado", "error"):
        raise HTTPException(status_code=409, detail="Solo se puede publicar una pendiente o con error")
    try:
        result = _do_publish(conn, str(row.get("image_url") or ""), str(row.get("caption") or ""))
    except HTTPException as exc:
        _mark_error(user.id, post_id, str(exc.detail))
        raise
    _mark_published(user.id, post_id, result["container_id"], result["media_id"])
    return PublishResponse(
        estado="publicado",
        media_id=result["media_id"],
        container_id=result["container_id"],
    )


@router.post("/scheduled/run-due", response_model=RunDueResponse)
def run_due(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> RunDueResponse:
    """Worker: publica todas las vencidas del dueño. Lo llama un cron o el dashboard."""
    conn = _require_publisher(user.id)
    due = _due_posts(user.id)
    published = 0
    errors: list[dict] = []
    for row in due:
        post_id = str(row["id"])
        try:
            result = _do_publish(
                conn, str(row.get("image_url") or ""), str(row.get("caption") or "")
            )
        except HTTPException as exc:
            _mark_error(user.id, post_id, str(exc.detail))
            errors.append({"id": post_id, "error": str(exc.detail)})
            continue
        _mark_published(user.id, post_id, result["container_id"], result["media_id"])
        published += 1
    return RunDueResponse(revisados=len(due), publicados=published, errores=errors)
