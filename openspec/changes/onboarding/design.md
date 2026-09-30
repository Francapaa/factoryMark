## Context

See proposal.md (Why). Current state: `tools/places.py` exposes anchor resolution (top-1 Search) used per-request by the branched researcher; `AnalyzeRequest` carries `business_name` but nothing persists it; auth yields `CurrentUser.id` (Neon `sub`) on every protected call; frontend `/app` renders `AnalyzeForm` immediately after login with no setup step. Neon Postgres exists with user credentials; the app owns no tables yet.

## Goals / Non-Goals

**Goals:**

- "¿Cuál es tu local?" answered once, confirmed visually by the owner, saved, reused.
- Agents never run on unconfirmed businesses (explicit gate, not silent fixtures).
- Raw SQL only — readable queries, no ORM (owner decision).

**Non-Goals:**

- Multi-local, premium tiers, billing (recorded as future; schema must not block them).
- Embedded maps, brand-kit editor, photo upload by owner (separate changes).
- Changing per-request anchor behavior for API callers that already pass confirmed data.

## Decisions

- **Reuse, don't duplicate, anchor resolution**: `POST /api/businesses/resolve` calls the same resolver as the researcher (same function, same cache namespace, same 404 semantics). One implementation, two callers.
- **Photo via backend proxy, never key in browser**: confirmation screen needs the shop photo; Places photo URLs require the server key, so `GET /api/businesses/photo?photo_ref=…` streams bytes with the key server-side. The browser never sees `GOOGLE_PLACES_API_KEY`.
- **Maps link, not embed**: confirmation shows address + photo + "ver en Google Maps" link (free). Embedded Maps JS/Embed API (billing + key exposure questions) deferred until validation demands it.
- **Raw `psycopg` with a tiny `db.py`**: one connection pool from `DATABASE_URL`, plain parameterized SQL in named functions (`get_my_business`, `save_my_business`), DDL as a checked-in `schema.sql` applied explicitly (no auto-migrate magic). Owner decision: queries must stay readable.
- **One row per user, enforced in DB**: `UNIQUE(owner_id)` on `app.negocios`. Save = upsert (re-onboarding replaces the single row). Multi-local later = drop the constraint + add plan check; no data migration beyond that.
- **Gate at the API boundary, not inside nodes**: `/api/analyze` resolves the effective business (saved row, or explicit confirmed payload) and returns 409 `onboarding_incompleto` when none exists. Nodes keep assuming confirmed input (their existing specs unchanged).
- **Snapshot anchor data at confirm time**: name/address/latlng/rating/photo_ref copied into the row so the app renders instantly without re-calling Places; refresh is a future change.

## Risks / Trade-offs

- [Risk] Anchor ambiguity (two same-named shops) → Mitigation: confirm screen shows photo + address + Maps link; user picks, not the model. Unresolvable → 404, never guess.
- [Risk] Raw SQL drift (queries scattered) → Mitigation: all SQL lives in `db.py` named functions; tests run against a real (ephemeral) Postgres, never mocks that hide SQL errors.
- [Risk] `DATABASE_URL` misconfigured → Mitigation: fail fast at startup with a clear message when the var is missing; `/health` reports `db_configured` without leaking the URL.
- [Risk] Photo proxy abused as open relay → Mitigation: accepts only `photo_ref` opaque tokens, no arbitrary URLs; response is image bytes with cache headers.

## Open Questions

- Re-confirm cadence: should the app ever ask "¿seguís en este local?" (e.g. yearly), or is the snapshot permanent until the user changes it? Proposed: permanent until user edits; confirm with owner.
- Display name vs legal Maps name: if the owner renames their shop in-app, does analysis keep using the Maps anchor name? Proposed: anchor stays canonical, display name is cosmetic.
