## Why

Today every analysis starts from zero: the user types business data per request, nothing is persisted, and there is no `Negocio` concept — the pipeline cannot know whose shop it works for. The `competitor-research` spec already requires a mandatory business anchor, but the anchor is resolved and discarded per request. To run agents for a real owner (and later charge per business), the system must know the owner's place: name + location in, user-confirmed Maps match, saved once, reused everywhere.

## What Changes

- New `POST /api/businesses/resolve`: name + zone in, top-1 anchored candidate out (place_id, name, address, rating, hours summary, photo via backend proxy, lat/lng) — exactly 1 cached Places Search call, 404 when unresolvable, never fabricated.
- New `Negocio` persistence in Neon (`app` schema, raw SQL via `psycopg`, no ORM — owner decision): id, owner_id (Neon `sub`), name, type, channel, zone, anchor place_id + snapshot, brand_kit, timestamps. Exactly one business per user (unique `owner_id`); multi-local reserved for future premium tiers.
- New `POST /api/businesses` (save confirmed business), `GET /api/businesses/mine` (read mine): upsert-single semantics.
- Pipeline gate: agents require a completed onboarding — a confirmed, saved business — and refuse otherwise with an explicit "complete onboarding" error instead of running on unconfirmed input.
- Frontend onboarding flow: form (name + location) → "¿Este es tu local?" confirm screen (photo, address, Maps link) → saved → app unlocked.

## Capabilities

### New Capabilities

- `business-resolve`: Cheap anchor lookup for onboarding — 1 cached Search call, explicit 404, photo served through backend proxy (key never leaks to the browser), Maps link (free) instead of embedded map.
- `business-onboarding`: Optional flow with mandatory completion for agent runs — form, visual confirm, save; without a saved business the pipeline answers 409 "onboarding incompleto" instead of analyzing.
- `business-storage`: Single-business persistence — raw-SQL `psycopg` layer, `app.negocios` table, unique owner, snapshot of anchor data at confirm time.

### Modified Capabilities

- `competitor-research`: anchor resolution reuses the resolve logic (shared function, same cache namespace); per-request anchor behavior unchanged for callers that already supply a confirmed `business_id`.
- `orchestration`: `run_analysis` accepts an optional confirmed business (anchor + snapshot) and skips re-resolution when present.

## Impact

- Code: new `backend/src/db.py` (psycopg pool + `app.negocios` DDL), `backend/src/api/businesses.py` (resolve/save/mine/photo-proxy), photo proxy route, frontend onboarding pages/components. New dependency: `psycopg[binary]`. New env: `DATABASE_URL` (already in user `.env`, add to `.env.example`).
- DB: one new table `app.negocios`; zero migrations on existing objects (Neon auth schema untouched).
- Cost: resolve = 1 Search call per onboarding (cached 7 days); photo proxy reuses cached Details photos, no extra billing.
- Explicitly out of scope: multi-local (premium, later), embedded Maps (link only), brand-kit editor, WhatsApp delivery.
