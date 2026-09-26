## Why

The Researcher agent runs on hardcoded fixtures (2 cafés in Palermo) and the existing Places Search client is not wired into the pipeline, so every analysis returns mock data. Real competitor signals — reviews, hours, photos, web presence — are needed before the golden-set evaluation and any demo to real shop owners mean anything.

## What Changes

- Add `fetch_place_details` to the Places client (real reviews, opening hours, photos) with the same 7-day disk cache, retry, and `MockTransport`-friendly design as `search_competitors`.
- Add an optional Tavily web-search tool for off-Maps signals (own website, menus/prices, delivery profiles, press mentions, social profile links), disabled by default and capped per analysis.
- Wire `researcher_node` to Search + Details + Tavily (when enabled), keeping fixture fallback when no API keys are configured so local dev and tests stay free.
- Wire `POST /api/analyze` to the LangGraph pipeline (`graph.run_analysis`) instead of returning the empty stub.
- Extend `Competitor` state with the new fields (hours, photos, website, web signals) in a backward-compatible way.
- Cover everything with tests (mocked transports, no real API calls) and add a script to run the golden set against the real pipeline.

## Capabilities

### New Capabilities

- `competitor-research`: Real competitor data collection for the Researcher agent — Google Maps (Places Search + Details: competitors, reviews, hours, photos) plus Tavily web signals, with caching, cost caps, fixture fallback, and pipeline wiring.

### Modified Capabilities

(none — no existing specs under `openspec/specs/` yet; this is the first change)

## Impact

- Affected code: `backend/src/tools/places.py` (new `fetch_place_details`), new `backend/src/tools/tavily.py`, `backend/src/agents/researcher.py`, `backend/src/state.py` (`Competitor`), `backend/src/main.py` (`/api/analyze`), `backend/src/graph.py` (passthrough of new state), `backend/.env.example`, `backend/README.md`.
- New dependency: `tavily` HTTP client via `httpx` (no new SDK required; plain REST) + `TAVILY_API_KEY` env var.
- APIs: `POST /api/analyze` response shape gains new optional fields; existing fields unchanged.
- Cost: Places Details calls billed per place (capped by `max_competitors`, cached 7 days); Tavily capped per analysis and off by default. No real calls in tests.
- Explicitly out of scope: social-media performance data (post frequency, engagement) — stays a paid Phase 2 via Apify; LLM copy generation; real publishing.
