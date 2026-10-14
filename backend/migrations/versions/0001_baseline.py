"""Baseline: app.negocios + app.instagram_conexiones + app.publicaciones.

DDL en SQL crudo (decisión del proyecto: sin ORM). Idempotente
(IF NOT EXISTS) para adoptar sin romper bases ya creadas a mano.
"""

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.negocios (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            business_type TEXT NOT NULL DEFAULT '',
            sales_channel TEXT NOT NULL DEFAULT 'local',
            zone TEXT NOT NULL DEFAULT '',
            anchor_place_id TEXT NOT NULL,
            anchor_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            brand_kit JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.instagram_conexiones (
            owner_id TEXT PRIMARY KEY,
            ig_user_id TEXT NOT NULL DEFAULT '',
            username TEXT NOT NULL DEFAULT '',
            access_token_enc TEXT NOT NULL,
            scopes TEXT NOT NULL DEFAULT '',
            obtained_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_in_s INTEGER NOT NULL DEFAULT 5184000,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.publicaciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id TEXT NOT NULL,
            copy_text TEXT NOT NULL DEFAULT '',
            hashtags TEXT[] NOT NULL DEFAULT '{}',
            image_url TEXT NOT NULL DEFAULT '',
            caption TEXT NOT NULL DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'programado'
                CHECK (estado IN ('borrador', 'aprobado', 'programado', 'publicado', 'rechazado', 'error')),
            programada_para TIMESTAMPTZ NULL,
            container_id TEXT NULL,
            external_id TEXT NULL,
            error TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            published_at TIMESTAMPTZ NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_publicaciones_owner_estado
            ON app.publicaciones(owner_id, estado)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_publicaciones_due
            ON app.publicaciones(owner_id, programada_para)
            WHERE estado = 'programado'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_publicaciones_due")
    op.execute("DROP INDEX IF EXISTS idx_publicaciones_owner_estado")
    op.execute("DROP TABLE IF EXISTS app.publicaciones")
    op.execute("DROP TABLE IF EXISTS app.instagram_conexiones")
    op.execute("DROP TABLE IF EXISTS app.negocios")
