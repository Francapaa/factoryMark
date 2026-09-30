"""Capa de datos del negocio del dueño: SQL crudo, sin ORM (decisión del owner).

Todo acceso vive en funciones nombradas con SQL parametrizado visible.
DDL: `backend/schema.sql` (aplicado explícito, sin auto-migrate).
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
