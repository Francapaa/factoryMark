## Purpose

Persists the owner's confirmed shop in Neon with readable raw SQL only — no ORM (owner decision). One row per user today; schema shaped so premium multi-local is a constraint change, not a migration.

## ADDED Requirements

### Requirement: Negocios table in app schema

The system SHALL own table `app.negocios` with columns: `id` (uuid, pk), `owner_id` (text, UNIQUE, Neon `sub`), `name`, `business_type`, `sales_channel`, `zone`, `anchor_place_id`, `anchor_snapshot` (jsonb: address, lat/lng, rating, photo_ref, resolved_at), `brand_kit` (jsonb, nullable), `created_at`, `updated_at`. DDL lives in a checked-in `schema.sql`, applied explicitly.

#### Scenario: Schema applies cleanly on empty DB

- **WHEN** `schema.sql` runs against a fresh Neon database
- **THEN** `app.negocios` exists with the unique constraint on `owner_id` and no other app objects are created

### Requirement: Raw-SQL data layer without ORM

The system SHALL implement all access as parameterized SQL in named `db.py` functions (`get_my_business(owner_id)`, `save_my_business(owner_id, …)`); no ORM models, query builders, or auto-migrations.

#### Scenario: Queries are readable SQL

- **WHEN** the data layer is reviewed
- **THEN** every database operation is a visible SQL string with parameters — no generated or hidden queries

### Requirement: Save and read endpoints for the owner's single business

The system SHALL expose `POST /api/businesses` (save confirmed business → upsert by `owner_id`) and `GET /api/businesses/mine` (return it or 404 `sin_negocio`), both auth-required and strictly scoped to the caller's `owner_id`.

#### Scenario: Save then read roundtrip

- **WHEN** an authenticated user saves a confirmed business and then reads it
- **THEN** the read returns exactly the saved fields including the anchor snapshot

#### Scenario: Users never see each other's business

- **WHEN** two different users save businesses
- **THEN** each `GET /mine` returns only its own row (enforced by `WHERE owner_id = caller`, tested)

### Requirement: Startup fails fast on missing database config

The system SHALL refuse to boot business routes when `DATABASE_URL` is absent (clear error at startup) and SHALL report `db_configured` (boolean only, never the URL) in `/health`.

#### Scenario: Missing DATABASE_URL

- **WHEN** the backend starts without `DATABASE_URL`
- **THEN** it fails fast with a message naming the missing variable instead of erroring on first request
