"""Historial de análisis + entidades normalizadas por negocio.

Cada corrida queda en app.analisis. Competidores y oportunidades se guardan
una sola vez por negocio (clave estable) y referencian la primera y la última
corrida en la que aparecieron. Así el dashboard lee la última foto sin
recalcular y el historial queda disponible para métricas futuras.

DDL en SQL crudo, idempotente como 0001_baseline.
"""

from alembic import op

revision = "0002_analysis_cache"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.analisis (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            business_id UUID NOT NULL
                REFERENCES app.negocios(id) ON DELETE CASCADE,
            competitors_count INTEGER NOT NULL DEFAULT 0,
            opportunities_count INTEGER NOT NULL DEFAULT 0,
            new_competitors_count INTEGER NOT NULL DEFAULT 0,
            new_opportunities_count INTEGER NOT NULL DEFAULT 0,
            clusters JSONB NOT NULL DEFAULT '[]'::jsonb,
            draft_post JSONB NULL,
            meta JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_first_run BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.competidores (
            business_id UUID NOT NULL
                REFERENCES app.negocios(id) ON DELETE CASCADE,
            place_id TEXT NOT NULL,
            name TEXT NOT NULL,
            rating DOUBLE PRECISION NULL,
            user_ratings_total INTEGER NOT NULL DEFAULT 0,
            address TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'maps'
                CHECK (source IN ('maps', 'web')),
            distance_m DOUBLE PRECISION NULL,
            opening_hours JSONB NOT NULL DEFAULT '[]'::jsonb,
            photos JSONB NOT NULL DEFAULT '[]'::jsonb,
            website TEXT NOT NULL DEFAULT '',
            reviews_fetched INTEGER NOT NULL DEFAULT 0,
            latitude DOUBLE PRECISION NULL,
            longitude DOUBLE PRECISION NULL,
            score DOUBLE PRECISION NULL,
            cached BOOLEAN NOT NULL DEFAULT false,
            first_seen_run_id UUID NOT NULL
                REFERENCES app.analisis(id) ON DELETE CASCADE,
            last_seen_run_id UUID NOT NULL
                REFERENCES app.analisis(id) ON DELETE CASCADE,
            first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (business_id, place_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app.oportunidades (
            business_id UUID NOT NULL
                REFERENCES app.negocios(id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            title TEXT NOT NULL,
            evidence TEXT NOT NULL,
            confidence TEXT NOT NULL
                CHECK (confidence IN ('alta', 'media', 'baja')),
            first_seen_run_id UUID NOT NULL
                REFERENCES app.analisis(id) ON DELETE CASCADE,
            last_seen_run_id UUID NOT NULL
                REFERENCES app.analisis(id) ON DELETE CASCADE,
            first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (business_id, key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_analisis_business_created
            ON app.analisis(business_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_competidores_business_last_seen
            ON app.competidores(business_id, last_seen_run_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_oportunidades_business_last_seen
            ON app.oportunidades(business_id, last_seen_run_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_oportunidades_business_last_seen")
    op.execute("DROP INDEX IF EXISTS idx_competidores_business_last_seen")
    op.execute("DROP INDEX IF EXISTS idx_analisis_business_created")
    op.execute("DROP TABLE IF EXISTS app.oportunidades")
    op.execute("DROP TABLE IF EXISTS app.competidores")
    op.execute("DROP TABLE IF EXISTS app.analisis")
