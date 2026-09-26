## Why

The Researcher agent runs on hardcoded fixtures (2 cafés in Palermo) and the existing Places Search client is not wired into the pipeline, so every analysis returns mock data. Worse, the input has no specific business: without a `business_name` anchor there is no way to find *nearby* competitors, and online stores (which compete on web/social, not geography) are not covered at all. Real competitor signals — anchored by business and sales channel — are needed before the golden-set evaluation and any demo to real shop owners mean anything.

## What Changes

- Make `business_name` a mandatory input (`400` when missing): the analysis anchors on the specific business, resolved via Places Search (top-1), with an explicit error when it cannot be resolved — never a silent fixture fallback.
- Add a mandatory `sales_channel` enum (`local | online | mixto`): `local` competes by proximity (Places anchor → `locationBias` circle → Details), `online` competes on web/social (Tavily-first + Places best-effort), `mixto` runs both branches and merges with source tags.
- Add `fetch_place_details` to the Places client (real reviews, opening hours, photos) with the same 7-day disk cache, retry, and `MockTransport`-friendly design as `search_competitors`.
- Add a Tavily web-search tool: primary source for `online`/`mixto`, optional enrichment for `local`; capped per analysis, cached, failure-isolated.
- Wire `researcher_node` to the branched pipeline, keeping fixture fallback ONLY when no API keys are configured so local dev and tests stay free.
- Wire `POST /api/analyze` to the LangGraph pipeline (`graph.run_analysis`) instead of returning the empty stub; wire the frontend form to the real endpoint with the three input fields.
- Extend `Competitor` state with the new fields (hours, photos, website, distance, source) in a backward-compatible way.
- Cover everything with tests (mocked transports, no real API calls) and add a script to run the golden set against the real pipeline.

## Capabilities

### New Capabilities

- `competitor-research`: Real competitor data collection for the Researcher agent — mandatory business anchor + sales-channel branching (local proximity via Maps Search + Details, online competition via Tavily web signals), with caching, cost caps, fixture fallback (keyless only), and pipeline wiring.

### Modified Capabilities

(none — no existing specs under `openspec/specs/` yet; this is the first change)

## Impact

- Affected code: `backend/src/tools/places.py` (new `fetch_place_details`), new `backend/src/tools/tavily.py`, `backend/src/agents/researcher.py`, `backend/src/state.py` (`Competitor`), `backend/src/main.py` (`/api/analyze`), `backend/src/graph.py` (passthrough of new state), `backend/.env.example`, `backend/README.md`.
- New dependency: `tavily` HTTP client via `httpx` (no new SDK required; plain REST) + `TAVILY_API_KEY` env var.
- APIs: `POST /api/analyze` response shape gains new optional fields; existing fields unchanged.
- Cost: Places Details calls billed per place (capped by `max_competitors`, cached 7 days); Tavily mandatory for `online`/`mixto` (~$0.01/search, 3–5 queries per analysis, cached), optional for `local`. No real calls in tests.
- Explicitly out of scope (Phase 2 via Apify, paid): social-media performance data — post frequency, content mix, engagement metrics. Rationale: Meta's official API only exposes the owner's own accounts (useless for competitor intel) and direct scraping violates ToS and gets blocked; Apify/Phantombuster provide public-post data (captions, likes, cadence) as a compliant paid API. This change only surfaces social *profile links* via Tavily, never performance metrics. Also out of scope: LLM copy generation; real publishing.
