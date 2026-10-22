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


def _row_to_competitor(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "place_id": row["place_id"],
        "name": row["name"],
        "rating": row.get("rating"),
        "user_ratings_total": int(row.get("user_ratings_total") or 0),
        "address": row.get("address") or "",
        "cached": bool(row.get("cached")),
        "source": row.get("source") or "maps",
        "distance_m": row.get("distance_m"),
        "opening_hours": list(row.get("opening_hours") or []),
        "photos": list(row.get("photos") or []),
        "website": row.get("website") or "",
        "reviews_fetched": int(row.get("reviews_fetched") or 0),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "score": row.get("score"),
        "is_new": bool(row.get("is_new")),
    }


def _row_to_opportunity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": row["key"],
        "title": row["title"],
        "evidence": row["evidence"],
        "confidence": row["confidence"],
        "is_new": bool(row.get("is_new")),
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
    """Guarda (upsert) el único negocio del dueño. Re-onboarding reemplaza la fila.

    Si cambia la identidad del negocio (nombre, tipo, canal, zona o ancla), los
    análisis guardados dejan de ser válidos y se borran en la misma transacción.
    """
    import json

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, business_type, sales_channel, zone, anchor_place_id
              FROM app.negocios
             WHERE owner_id = %(owner_id)s
             FOR UPDATE
            """,
            {"owner_id": owner_id},
        )
        existing = cur.fetchone()
        if existing is not None:
            incoming = {
                "name": name,
                "business_type": business_type,
                "sales_channel": sales_channel,
                "zone": zone,
                "anchor_place_id": anchor_place_id,
            }
            if any(str(existing[key]) != str(value) for key, value in incoming.items()):
                cur.execute(
                    "DELETE FROM app.analisis WHERE business_id = %(business_id)s::uuid",
                    {"business_id": str(existing["id"])},
                )
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


def save_analysis_run(
    business_id: str,
    *,
    competitors: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    draft_post: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Persiste una corrida completa y devuelve qué entidades son nuevas.

    Todo ocurre en una transacción: si falla cualquier insert, no queda una
    corrida a medias ni entidades huérfanas.
    """
    import json

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM app.analisis WHERE business_id = %(business_id)s::uuid
            ) AS has_runs
            """,
            {"business_id": business_id},
        )
        previous = cur.fetchone()
        assert previous is not None
        is_first_run = not previous["has_runs"]

        cur.execute(
            """
            INSERT INTO app.analisis (
                business_id, clusters, draft_post, meta, is_first_run
            )
            VALUES (
                %(business_id)s::uuid, %(clusters)s::jsonb,
                %(draft_post)s::jsonb, %(meta)s::jsonb, %(is_first_run)s
            )
            RETURNING id, created_at
            """,
            {
                "business_id": business_id,
                "clusters": json.dumps(clusters),
                "draft_post": json.dumps(draft_post) if draft_post is not None else None,
                "meta": json.dumps(meta),
                "is_first_run": is_first_run,
            },
        )
        run = cur.fetchone()
        assert run is not None
        run_id = str(run["id"])

        new_competitor_ids: list[str] = []
        for comp in competitors:
            cur.execute(
                """
                INSERT INTO app.competidores (
                    business_id, place_id, name, rating, user_ratings_total,
                    address, source, distance_m, opening_hours, photos, website,
                    reviews_fetched, latitude, longitude, score, cached,
                    first_seen_run_id, last_seen_run_id, first_seen_at, last_seen_at
                ) VALUES (
                    %(business_id)s::uuid, %(place_id)s, %(name)s, %(rating)s,
                    %(user_ratings_total)s, %(address)s, %(source)s, %(distance_m)s,
                    %(opening_hours)s::jsonb, %(photos)s::jsonb, %(website)s,
                    %(reviews_fetched)s, %(latitude)s, %(longitude)s, %(score)s,
                    %(cached)s, %(run_id)s::uuid, %(run_id)s::uuid, now(), now()
                )
                ON CONFLICT (business_id, place_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    rating = EXCLUDED.rating,
                    user_ratings_total = EXCLUDED.user_ratings_total,
                    address = EXCLUDED.address,
                    source = EXCLUDED.source,
                    distance_m = EXCLUDED.distance_m,
                    opening_hours = EXCLUDED.opening_hours,
                    photos = EXCLUDED.photos,
                    website = EXCLUDED.website,
                    reviews_fetched = EXCLUDED.reviews_fetched,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    score = EXCLUDED.score,
                    cached = EXCLUDED.cached,
                    last_seen_run_id = EXCLUDED.last_seen_run_id,
                    last_seen_at = now()
                RETURNING (first_seen_run_id = %(run_id)s::uuid) AS is_new
                """,
                {
                    "business_id": business_id,
                    "run_id": run_id,
                    "place_id": comp["place_id"],
                    "name": comp["name"],
                    "rating": comp.get("rating"),
                    "user_ratings_total": int(comp.get("user_ratings_total") or 0),
                    "address": comp.get("address") or "",
                    "source": comp.get("source") or "maps",
                    "distance_m": comp.get("distance_m"),
                    "opening_hours": json.dumps(comp.get("opening_hours") or []),
                    "photos": json.dumps(comp.get("photos") or []),
                    "website": comp.get("website") or "",
                    "reviews_fetched": int(comp.get("reviews_fetched") or 0),
                    "latitude": comp.get("latitude"),
                    "longitude": comp.get("longitude"),
                    "score": comp.get("score"),
                    "cached": bool(comp.get("cached")),
                },
            )
            row = cur.fetchone()
            if row and row["is_new"] and not is_first_run:
                new_competitor_ids.append(comp["place_id"])

        new_opportunity_keys: list[str] = []
        for opp in opportunities:
            cur.execute(
                """
                INSERT INTO app.oportunidades (
                    business_id, key, title, evidence, confidence,
                    first_seen_run_id, last_seen_run_id, first_seen_at, last_seen_at
                ) VALUES (
                    %(business_id)s::uuid, %(key)s, %(title)s, %(evidence)s,
                    %(confidence)s, %(run_id)s::uuid, %(run_id)s::uuid, now(), now()
                )
                ON CONFLICT (business_id, key) DO UPDATE SET
                    title = EXCLUDED.title,
                    evidence = EXCLUDED.evidence,
                    confidence = EXCLUDED.confidence,
                    last_seen_run_id = EXCLUDED.last_seen_run_id,
                    last_seen_at = now()
                RETURNING (first_seen_run_id = %(run_id)s::uuid) AS is_new
                """,
                {
                    "business_id": business_id,
                    "run_id": run_id,
                    "key": opp["key"],
                    "title": opp["title"],
                    "evidence": opp["evidence"],
                    "confidence": opp["confidence"],
                },
            )
            row = cur.fetchone()
            if (
                row
                and row["is_new"]
                and not is_first_run
                and opp["key"] != "none"
            ):
                new_opportunity_keys.append(opp["key"])

        cur.execute(
            """
            UPDATE app.analisis
               SET competitors_count = %(competitors_count)s,
                   opportunities_count = %(opportunities_count)s,
                   new_competitors_count = %(new_competitors_count)s,
                   new_opportunities_count = %(new_opportunities_count)s
             WHERE id = %(run_id)s::uuid
            """,
            {
                "run_id": run_id,
                "competitors_count": len(competitors),
                "opportunities_count": len(opportunities),
                "new_competitors_count": len(new_competitor_ids),
                "new_opportunities_count": len(new_opportunity_keys),
            },
        )
        conn.commit()

    return {
        "analysis": {
            "id": run_id,
            "analyzed_at": run["created_at"].isoformat(),
            "competitors_count": len(competitors),
            "opportunities_count": len(opportunities),
            "new_competitors": len(new_competitor_ids),
            "new_opportunities": len(new_opportunity_keys),
        },
        "new_competitor_ids": new_competitor_ids,
        "new_opportunity_keys": new_opportunity_keys,
    }


def get_latest_analysis(business_id: str) -> dict[str, Any] | None:
    """Última corrida guardada + las entidades que siguen vigentes en ella."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, competitors_count, opportunities_count,
                   new_competitors_count, new_opportunities_count,
                   clusters, draft_post, meta, is_first_run, created_at
              FROM app.analisis
             WHERE business_id = %(business_id)s::uuid
             ORDER BY created_at DESC, id DESC
             LIMIT 1
            """,
            {"business_id": business_id},
        )
        run = cur.fetchone()
        if run is None:
            return None
        run_id = str(run["id"])
        is_first_run = bool(run["is_first_run"])
        cur.execute(
            """
            SELECT place_id, name, rating, user_ratings_total, address, source,
                   distance_m, opening_hours, photos, website, reviews_fetched,
                   latitude, longitude, score, cached,
                   (first_seen_run_id = %(run_id)s::uuid
                    AND NOT %(is_first_run)s::boolean) AS is_new
              FROM app.competidores
             WHERE business_id = %(business_id)s::uuid
               AND last_seen_run_id = %(run_id)s::uuid
             ORDER BY score DESC NULLS LAST, distance_m ASC NULLS LAST, name ASC
            """,
            {
                "business_id": business_id,
                "run_id": run_id,
                "is_first_run": is_first_run,
            },
        )
        competitors = [_row_to_competitor(row) for row in cur.fetchall()]
        cur.execute(
            """
            SELECT key, title, evidence, confidence,
                   (first_seen_run_id = %(run_id)s::uuid
                    AND NOT %(is_first_run)s::boolean
                    AND key <> 'none') AS is_new
              FROM app.oportunidades
             WHERE business_id = %(business_id)s::uuid
               AND last_seen_run_id = %(run_id)s::uuid
             ORDER BY CASE confidence
                        WHEN 'alta' THEN 0
                        WHEN 'media' THEN 1
                        ELSE 2
                      END,
                      first_seen_at ASC
            """,
            {
                "business_id": business_id,
                "run_id": run_id,
                "is_first_run": is_first_run,
            },
        )
        opportunities = [_row_to_opportunity(row) for row in cur.fetchall()]

    return {
        "analysis": {
            "id": run_id,
            "analyzed_at": run["created_at"].isoformat(),
            "competitors_count": int(run["competitors_count"]),
            "opportunities_count": int(run["opportunities_count"]),
            "new_competitors": int(run["new_competitors_count"]),
            "new_opportunities": int(run["new_opportunities_count"]),
        },
        "competitors": competitors,
        "opportunities": opportunities,
        "clusters": list(run["clusters"] or []),
        "draft_post": run["draft_post"],
        "meta": run["meta"] or {},
    }


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
