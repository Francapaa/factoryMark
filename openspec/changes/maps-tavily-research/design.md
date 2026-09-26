## Context

See proposal.md (Why). Current state: `tools/places.py` implements Search-only (`places:searchText`) with 7-day disk cache, tenacity retry, and `httpx.MockTransport` tests; `agents/researcher.py` returns hardcoded fixtures and never calls it; `main.py:/api/analyze` returns an empty stub ignoring `graph.py`; `Competitor` has only `place_id/name/rating/user_ratings_total/address/cached`. No web-search client exists.

## Goals / Non-Goals

**Goals:**

- Real reviews/hours/photos per competitor via Places Details (New API), same cost discipline as Search.
- Optional Tavily web signals, off by default, capped, failure-isolated.
- One wired path: endpoint → graph → real researcher → analyst/strategist/creator/publisher unchanged.
- Golden set runnable against the real pipeline.

**Non-Goals:**

- Social-media performance metrics (Phase 2, Apify) — Tavily only surfaces profile *links*, never engagement data.
- LLM copy, real publishing, pricing-intelligence structured extraction, frontend changes beyond displaying new optional fields.
- Migrating NLP to sentence-transformers/HDBSCAN (separate future change).

## Decisions

- **Places Details via `places/{id}` GET (New API) with explicit `X-Goog-FieldMask`** (`reviews,regularOpeningHours,photos,websiteUri`) instead of the legacy Details endpoint: one key, one billing model, field mask keeps responses small. Alternative (legacy `Place Details` API) rejected — different key regime and heavier payloads.
- **Separate cache namespace for Details** (`details_<place_id>.json`) instead of reusing the Search query cache: Search keys are per-query, Details per-place; mixing them would poison TTL semantics. Same 7-day TTL and `saved_at` envelope.
- **Tavily as plain `httpx` REST (`/search` + `include_answer=false`) instead of the `tavily-python` SDK**: one less dependency, same `MockTransport` test pattern as Places, full control over caps/timeouts. Query shaped as `"<business_type> <zone> <competitor name>"` with `search_depth="basic"` to minimize cost; `max_results` capped.
- **Researcher orchestration branches on `sales_channel`**: `local` = resolve anchor → Search with `locationBias` circle → cap → Details fan-in (sequential, stays under QPS); `online` = Tavily query pack first (same-product sellers, prices, marketplaces, social links) + Places best-effort; `mixto` = both, merged with `source` tags. Alternatives (inferring channel from text, parallel fan-in) rejected: inference is fragile, parallelism adds throttling machinery for a demo-scale N≤10.
- **Anchor resolution reuses Places Search (`textQuery = business_name + zone`, top-1)** instead of Geocoding API: no extra SKU, same key and cache. Ambiguity risk (two same-named shops) mitigated by returning the top result plus its formatted address in `meta.anchor` so the user can verify; a future disambiguation step (ask user to pick) is noted but out of scope.
- **Mandatory inputs enforced by Pydantic (422) + explicit 404 for unresolvable anchor**: silent fixture fallback when keys exist would fabricate competitor intel — the worst failure mode for this product. Fixtures remain only for keyless dev/CI, flagged `stub=True`.
- **Fixture fallback preserved behind missing-key check** (not removed): local dev, CI, and golden-set dry runs stay free; `meta.stub` flag keeps honesty about data provenance.
- **`Competitor` extended with optional fields** (`opening_hours`, `photos`, `website`, `reviews_fetched`) rather than a new model: backward-compatible for frontend and existing tests; Pydantic `extra="ignore"`-safe.

## Risks / Trade-offs

- [Risk] Places Details returns at most ~5 reviews per place → clusters may be thin → Mitigation: aggregate across all competitors (10 places × 5 = ~50 texts, enough for TF-IDF/KMeans); document the ceiling in README.
- [Risk] Tavily snippets are noisy/stale → Mitigation: store source URL + published date with every signal; strategist rules never consume web signals in this change (display + evidence only). Online-mode opportunity quality therefore depends on review/Maps evidence where available — documented, not hidden.
- [Risk] Anchor ambiguity (same-named businesses) → Mitigation: `meta.anchor` exposes resolved address for user verification; disambiguation UI deferred to a later change.
- [Risk] Details fan-in multiplies Places billing (1 Search + N Details) → Mitigation: `max_competitors` cap + 7-day cache + `max_reviews_per_place` field limit; `/health` reports key presence so operators see what's billable.
- [Risk] New optional fields break the frontend contract → Mitigation: all new fields optional with defaults; existing response fields untouched.

## Migration Plan

1. Land behind safe defaults (`tavily_enabled=False`; no key → fixtures), so deploy is a no-op without keys.
2. Set `GOOGLE_PLACES_API_KEY` (+ optional `TAVILY_API_KEY`) in `backend/.env`; first real run warms the disk cache.
3. Rollback: unset keys → system reverts to fixture behavior; delete `backend/data/cache/details_*` to force refresh.
4. No DB migration (disk JSON cache only; new files, old entries still valid).

## Open Questions

- None blocking. Deferrable: exact Tavily `search_depth` tuning after seeing snippet quality on the 5 golden-set cases.
