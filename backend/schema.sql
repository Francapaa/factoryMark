-- FactoryMark: tabla del negocio del dueño (onboarding).
-- Aplicar explícitamente contra Neon (sin auto-migrate):
--   psql "$DATABASE_URL" -f schema.sql
-- Un solo negocio por usuario (multi-local = cambio de constraint, no migración).

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.negocios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id TEXT NOT NULL UNIQUE, -- Neon Auth `sub`, un local por usuario en v1
    name TEXT NOT NULL, -- nombre canónico de Google Maps (el dueño no renombra)
    business_type TEXT NOT NULL DEFAULT '',
    sales_channel TEXT NOT NULL DEFAULT 'local',
    zone TEXT NOT NULL DEFAULT '',
    anchor_place_id TEXT NOT NULL,
    anchor_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb, -- address, lat/lng, rating, photo_ref, resolved_at
    brand_kit JSONB, -- NULL en v1 (editor en otro change)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
