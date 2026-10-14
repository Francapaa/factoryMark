"""Capa de datos del negocio del dueño: SQL crudo, sin ORM (decisión del owner).

Todo acceso vive en funciones nombradas con SQL parametrizado visible.
DDL versionado: `backend/migrations/` (Alembic, `uv run alembic upgrade head`
manual desde backend/, sin auto-migrate).
"""

from __future__ import annotations

from typing import Any

from config import settings


def is_db_configured() -> bool:
    return bool(settings.database_url)


def _require_db() -> str:
    if not settings.database_url:
        raise RuntimeError(
            "Falta DATABASE_URL en backend/.env (negocio del dueño sin persistencia)"
        )
    return settings.database_url


def _connect():
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(_require_db(), row_factory=dict_row)


def _row_to_business(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "owner_id": row["owner_id"],
        "name": row["name"],
        "business_type": row["business_type"],
        "sales_channel": row["sales_channel"],
        "zone": row["zone"],
        "anchor_place_id": row["anchor_place_id"],
        "anchor_snapshot": row["anchor_snapshot"] or {},
        "brand_kit": row["brand_kit"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


def get_my_business(owner_id: str) -> dict[str, Any] | None:
    """Lee el único negocio del dueño. None si no completó onboarding."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, owner_id, name, business_type, sales_channel, zone,
                   anchor_place_id, anchor_snapshot, brand_kit,
                   created_at, updated_at
              FROM app.negocios
             WHERE owner_id = %(owner_id)s
            """,
            {"owner_id": owner_id},
        )
        row = cur.fetchone()
    return _row_to_business(row) if row else None


def save_my_business(
    owner_id: str,
    *,
    name: str,
    business_type: str,
    sales_channel: str,
    zone: str,
    anchor_place_id: str,
    anchor_snapshot: dict[str, Any],
    brand_kit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Guarda (upsert) el único negocio del dueño. Re-onboarding reemplaza la fila."""
    import json

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app.negocios
                (owner_id, name, business_type, sales_channel, zone,
                 anchor_place_id, anchor_snapshot, brand_kit, updated_at)
            VALUES
                (%(owner_id)s, %(name)s, %(business_type)s, %(sales_channel)s, %(zone)s,
                 %(anchor_place_id)s, %(anchor_snapshot)s::jsonb, %(brand_kit)s::jsonb, now())
            ON CONFLICT (owner_id) DO UPDATE SET
                name = EXCLUDED.name,
                business_type = EXCLUDED.business_type,
                sales_channel = EXCLUDED.sales_channel,
                zone = EXCLUDED.zone,
                anchor_place_id = EXCLUDED.anchor_place_id,
                anchor_snapshot = EXCLUDED.anchor_snapshot,
                brand_kit = EXCLUDED.brand_kit,
                updated_at = now()
            RETURNING id, owner_id, name, business_type, sales_channel, zone,
                      anchor_place_id, anchor_snapshot, brand_kit,
                      created_at, updated_at
            """,
            {
                "owner_id": owner_id,
                "name": name,
                "business_type": business_type,
                "sales_channel": sales_channel,
                "zone": zone,
                "anchor_place_id": anchor_place_id,
                "anchor_snapshot": json.dumps(anchor_snapshot),
                "brand_kit": json.dumps(brand_kit) if brand_kit is not None else None,
            },
        )
        row = cur.fetchone()
        conn.commit()
    assert row is not None
    return _row_to_business(row)


# --- Instagram v2: conexiones (token cifrado) + cola de programadas ---
# Todo SQL parametrizado visible, misma convención que negocios.


def _row_to_ig_connection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner_id": row["owner_id"],
        "ig_user_id": row.get("ig_user_id") or "",
        "username": row.get("username") or "",
        "access_token_enc": row["access_token_enc"],
        "scopes": row.get("scopes") or "",
        "obtained_at": row["obtained_at"].isoformat() if row.get("obtained_at") else None,
        "expires_in_s": row.get("expires_in_s") or 0,
    }


def save_instagram_connection(
    owner_id: str,
    *,
    ig_user_id: str,
    username: str,
    access_token_enc: str,
    scopes: str,
    expires_in_s: int,
) -> dict[str, Any]:
    """Upsert de la conexión IG del dueño (el token viaja ya cifrado)."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app.instagram_conexiones
                (owner_id, ig_user_id, username, access_token_enc, scopes,
                 obtained_at, expires_in_s, updated_at)
            VALUES
                (%(owner_id)s, %(ig_user_id)s, %(username)s, %(access_token_enc)s,
                 %(scopes)s, now(), %(expires_in_s)s, now())
            ON CONFLICT (owner_id) DO UPDATE SET
                ig_user_id = EXCLUDED.ig_user_id,
                username = EXCLUDED.username,
                access_token_enc = EXCLUDED.access_token_enc,
                scopes = EXCLUDED.scopes,
                obtained_at = now(),
                expires_in_s = EXCLUDED.expires_in_s,
                updated_at = now()
            RETURNING owner_id, ig_user_id, username, access_token_enc, scopes,
                      obtained_at, expires_in_s
            """,
            {
                "owner_id": owner_id,
                "ig_user_id": ig_user_id,
                "username": username,
                "access_token_enc": access_token_enc,
                "scopes": scopes,
                "expires_in_s": expires_in_s,
            },
        )
        row = cur.fetchone()
        conn.commit()
    assert row is not None
    return _row_to_ig_connection(row)


def refresh_instagram_connection_token(
    owner_id: str, *, access_token_enc: str, expires_in_s: int
) -> None:
    """Actualiza token + obtained_at tras un refresh (best-effort del endpoint)."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.instagram_conexiones
               SET access_token_enc = %(enc)s,
                   expires_in_s = %(expires)s,
                   obtained_at = now(),
                   updated_at = now()
             WHERE owner_id = %(owner_id)s
            """,
            {"enc": access_token_enc, "expires": expires_in_s, "owner_id": owner_id},
        )
        conn.commit()


def get_instagram_connection(owner_id: str) -> dict[str, Any] | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT owner_id, ig_user_id, username, access_token_enc, scopes,
                   obtained_at, expires_in_s
              FROM app.instagram_conexiones
             WHERE owner_id = %(owner_id)s
            """,
            {"owner_id": owner_id},
        )
        row = cur.fetchone()
    return _row_to_ig_connection(row) if row else None


def clear_instagram_connection(owner_id: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM app.instagram_conexiones WHERE owner_id = %(owner_id)s",
            {"owner_id": owner_id},
        )
        conn.commit()


def _row_to_post(row: dict[str, Any]) -> dict[str, Any]:
    def _iso(value: Any) -> str | None:
        return value.isoformat() if value is not None and hasattr(value, "isoformat") else value

    return {
        "id": str(row["id"]),
        "owner_id": row["owner_id"],
        "copy_text": row.get("copy_text") or "",
        "hashtags": list(row.get("hashtags") or []),
        "image_url": row.get("image_url") or "",
        "caption": row.get("caption") or "",
        "estado": row.get("estado") or "programado",
        "programada_para": _iso(row.get("programada_para")),
        "container_id": row.get("container_id"),
        "external_id": row.get("external_id"),
        "error": row.get("error"),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "published_at": _iso(row.get("published_at")),
    }


_POST_COLS = """
    id, owner_id, copy_text, hashtags, image_url, caption, estado,
    programada_para, container_id, external_id, error,
    created_at, updated_at, published_at
"""


def create_scheduled_post(
    owner_id: str,
    *,
    copy_text: str,
    hashtags: list[str],
    image_url: str,
    caption: str,
    programada_para: str,
) -> dict[str, Any]:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO app.publicaciones
                (owner_id, copy_text, hashtags, image_url, caption,
                 estado, programada_para, updated_at)
            VALUES
                (%(owner_id)s, %(copy_text)s, %(hashtags)s, %(image_url)s,
                 %(caption)s, 'programado', %(programada_para)s::timestamptz, now())
            RETURNING {_POST_COLS}
            """,
            {
                "owner_id": owner_id,
                "copy_text": copy_text,
                "hashtags": hashtags,
                "image_url": image_url,
                "caption": caption,
                "programada_para": programada_para,
            },
        )
        row = cur.fetchone()
        conn.commit()
    assert row is not None
    return _row_to_post(row)


def list_scheduled_posts(owner_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_POST_COLS}
              FROM app.publicaciones
             WHERE owner_id = %(owner_id)s
             ORDER BY created_at DESC
             LIMIT %(limit)s
            """,
            {"owner_id": owner_id, "limit": limit},
        )
        rows = cur.fetchall()
    return [_row_to_post(r) for r in rows]


def get_scheduled_post(owner_id: str, post_id: str) -> dict[str, Any] | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_POST_COLS}
              FROM app.publicaciones
             WHERE owner_id = %(owner_id)s AND id = %(post_id)s::uuid
            """,
            {"owner_id": owner_id, "post_id": post_id},
        )
        row = cur.fetchone()
    return _row_to_post(row) if row else None


def get_due_posts(owner_id: str) -> list[dict[str, Any]]:
    """Programadas vencidas (programada_para <= now), las que debe publicar el worker."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_POST_COLS}
              FROM app.publicaciones
             WHERE owner_id = %(owner_id)s
               AND estado = 'programado'
               AND programada_para IS NOT NULL
               AND programada_para <= now()
             ORDER BY programada_para ASC
            """,
            {"owner_id": owner_id},
        )
        rows = cur.fetchall()
    return [_row_to_post(r) for r in rows]


def mark_post_published(
    owner_id: str, post_id: str, *, container_id: str, external_id: str
) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.publicaciones
               SET estado = 'publicado',
                   container_id = %(container_id)s,
                   external_id = %(external_id)s,
                   error = NULL,
                   published_at = now(),
                   updated_at = now()
             WHERE owner_id = %(owner_id)s AND id = %(post_id)s::uuid
            """,
            {
                "owner_id": owner_id,
                "post_id": post_id,
                "container_id": container_id,
                "external_id": external_id,
            },
        )
        conn.commit()


def mark_post_error(owner_id: str, post_id: str, *, error: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.publicaciones
               SET estado = 'error',
                   error = %(error)s,
                   updated_at = now()
             WHERE owner_id = %(owner_id)s AND id = %(post_id)s::uuid
            """,
            {"owner_id": owner_id, "post_id": post_id, "error": error[:500]},
        )
        conn.commit()


def cancel_scheduled_post(owner_id: str, post_id: str) -> bool:
    """Cancela (marca rechazado, se conserva para auditoría). Solo si estaba programado."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.publicaciones
               SET estado = 'rechazado',
                   updated_at = now()
             WHERE owner_id = %(owner_id)s
               AND id = %(post_id)s::uuid
               AND estado = 'programado'
            """,
            {"owner_id": owner_id, "post_id": post_id},
        )
        updated = cur.rowcount or 0
        conn.commit()
    return updated > 0
