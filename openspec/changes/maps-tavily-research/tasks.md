## 1. Places Details client

- [ ] 1.1 Add `fetch_place_details(place_id, client?, cache_dir?)` to `backend/src/tools/places.py` (GET `places/{id}`, field mask `reviews,regularOpeningHours,photos,websiteUri`, per-place cache file, tenacity retry, `MockTransport`-compatible)
- [ ] 1.2 Extend `search_competitors` with optional `location_bias` (circle lat/lng + radius) and add `resolve_anchor(business_name, zone, ...)` (top-1, returns place_id + name + address + lat/lng); separate anchor cache namespace
- [ ] 1.3 Add tests `backend/tests/test_places_details.py` (cache hit = zero calls, retry on 429 then success, 4xx surfaces + records failure, bias serialized correctly, no real network)

## 2. Tavily web-signals tool

- [ ] 2.1 Add `backend/src/tools/tavily.py` (`search_web_signals(query, ...)` via plain `httpx`, capped results, timeout, returns URL + snippet + date; no-op without key) with disk cache + retry matching places.py conventions
- [ ] 2.2 Add settings (`tavily_api_key`, `tavily_enabled=False` for local enrichment, `tavily_max_queries`, `tavily_max_results`) + `.env.example` entries + tests with mocked transport (disabled/keyless = zero calls, failure isolated)

## 3. State + branching Researcher

- [ ] 3.1 Extend `AnalyzeRequest` (`business_name` + `sales_channel` required) and `Competitor` (optional `opening_hours`, `photos`, `website`, `reviews_fetched`, `distance_m`, `source`) in `backend/src/state.py`; extend `AgentState` with `business_name`, `sales_channel`, `anchor`, `web_signals`
- [ ] 3.2 Implement branching `researcher_node`: local (anchor → circle search → exclude anchor → Details → `reviews_by_place`), online (Tavily query pack first + Places best-effort), mixto (both + merge with source tags); keyless → fixtures with `stub=True`; unresolvable anchor → explicit error
- [ ] 3.3 Update `backend/tests/test_graph.py` for all three channels (mocked clients, cap respected, anchor excluded, fallback intact)

## 4. Endpoint + frontend + evaluation

- [ ] 4.1 Wire `POST /api/analyze` in `backend/src/main.py` to `graph.run_analysis` (input validation → 422/404, remove stub, keep auth, include `meta.trace` + `meta.anchor`)
- [ ] 4.2 Replace mock `AnalyzeForm` with real fetch (`business_name`, `business_type`, `zone`, `sales_channel` fields; loading/error states; render competitors, opportunities, draft from response)
- [ ] 4.3 Add golden-set runner script (`eval/run.py`) scoring the real pipeline with `eval/rubric.md` (add `business_name` + `sales_channel` cases); document baseline results
- [ ] 4.4 Update `backend/README.md` + `README.md` (new env vars, mandatory inputs, cost notes, Details 5-review ceiling, Phase 2 Apify note) and run full suite (`uv run pytest`) + manual frontend check
