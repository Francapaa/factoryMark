## 1. Places Details client

- [ ] 1.1 Add `fetch_place_details(place_id, client?, cache_dir?)` to `backend/src/tools/places.py` (GET `places/{id}`, field mask `reviews,regularOpeningHours,photos,websiteUri`, per-place cache file, tenacity retry, `MockTransport`-compatible)
- [ ] 1.2 Add tests `backend/tests/test_places_details.py` (cache hit = zero calls, retry on 429 then success, 4xx surfaces + records failure, no real network)

## 2. Tavily web-signals tool

- [ ] 2.1 Add `backend/src/tools/tavily.py` (`search_web_signals(query, ...)` via plain `httpx`, capped results, timeout, returns URL + snippet + date; no-op without key)
- [ ] 2.2 Add settings (`tavily_api_key`, `tavily_enabled=False`, `tavily_max_queries`, `tavily_max_results`) + `.env.example` entries + tests with mocked transport (disabled/keyless = zero calls, failure isolated)

## 3. State + Researcher wiring

- [ ] 3.1 Extend `Competitor` in `backend/src/state.py` with optional `opening_hours`, `photos`, `website`, `reviews_fetched`
- [ ] 3.2 Wire `researcher_node` to Search → cap → Details → `reviews_by_place` from real texts (+ Tavily when enabled), fixture fallback when keyless with `meta.stub`
- [ ] 3.3 Update `backend/tests/test_graph.py` for the real researcher path (mocked clients, cap respected, fallback intact)

## 4. Endpoint + evaluation

- [ ] 4.1 Wire `POST /api/analyze` in `backend/src/main.py` to `graph.run_analysis` (remove stub, keep auth, include `meta.trace`)
- [ ] 4.2 Add golden-set runner script (`eval/run.py`) scoring the real pipeline with `eval/rubric.md`; document baseline results
- [ ] 4.3 Update `backend/README.md` + `README.md` (new env vars, cost notes, Details 5-review ceiling) and run full suite (`uv run pytest`) + manual frontend check
