## 1. Specs (this change — project owner writes, no code)

- [x] 1.1 `proposal.md` — why (no Negocio concept), what (resolve + save + gate), impact
- [x] 1.2 `design.md` — shared resolver, photo proxy, Maps link, raw psycopg, one-row-per-user, API-boundary gate, snapshot
- [x] 1.3 `specs/business-resolve/spec.md` — cheap lookup, 404/422/400 semantics, photo proxy
- [x] 1.4 `specs/business-onboarding/spec.md` — 3-step flow, optional-but-gating, re-onboarding replaces
- [x] 1.5 `specs/business-storage/spec.md` — `app.negocios`, raw SQL, save/mine endpoints, fail-fast config

## 2. Implementation (other agents write the code)

- [ ] 2.1 DB: `backend/schema.sql` (`app.negocios` per spec) + `DATABASE_URL` in `backend/.env.example`
- [ ] 2.2 Backend: `backend/src/db.py` (psycopg pool, `get_my_business`, `save_my_business`, raw parameterized SQL only)
- [ ] 2.3 Backend: `backend/src/api/businesses.py` (resolve/save/mine/photo-proxy routes, auth-required, owner scoping)
- [ ] 2.4 Backend: gate in `/api/analyze` (409 `onboarding_incompleto` without confirmed business) + `db_configured` in `/health`
- [ ] 2.5 Frontend: onboarding pages (form → confirm with photo/address/Maps link → saved), `/app` unlock logic
- [ ] 2.6 Tests: resolve 404/422 (mocked transport), save/read roundtrip + isolation (ephemeral Postgres), gate 409, photo proxy rejects arbitrary URLs, zero real Places calls
- [ ] 2.7 New dependency `psycopg[binary]` via `uv add`; full suite green

## 3. Owner review + merge

- [ ] 3.1 Owner reviews this change (open: re-confirm cadence, display-vs-anchor name)
- [ ] 3.2 Merge to `main` only on explicit owner approval
