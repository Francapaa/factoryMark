## Purpose

Gives the Researcher agent real, affordable competitor data from Google Maps and the web, replacing hardcoded fixtures while keeping local development and tests free of API costs.

## ADDED Requirements

### Requirement: Places Details enrichment

The system SHALL enrich each competitor found by Places Search with real reviews, opening hours, and photos via the Places Details (Get Place) API, reusing the existing disk-cache, retry, and cap conventions.

#### Scenario: Details enrich a competitor

- **WHEN** the Researcher resolves a competitor with a valid `place_id`
- **THEN** the competitor includes up to `max_reviews_per_place` real review texts with author, rating, and timestamp, plus opening-hours summary and up to 3 photo references

#### Scenario: Details served from cache

- **WHEN** a fresh Details cache entry (TTL `places_cache_ttl_hours`) exists for a `place_id`
- **THEN** no billable Details request is made and the competitor is marked `cached=True`

#### Scenario: Failed Details call degrades gracefully

- **WHEN** the Details request fails after retries (4xx/5xx, timeout, missing key)
- **THEN** the competitor is kept with Search-only fields, the failure is recorded in `meta`, and the pipeline continues

### Requirement: Tavily web signals

The system SHALL optionally collect off-Maps web signals per analysis via Tavily (own website, menus/prices, delivery profiles, press mentions, social profile links) when `TAVILY_API_KEY` is configured and the feature is enabled.

#### Scenario: Web signals attached when enabled

- **WHEN** Tavily is enabled and a key is configured
- **THEN** the analysis includes per-analysis web signals (source URL + snippet each), capped at `tavily_max_queries` queries and `tavily_max_results` results each

#### Scenario: Tavily disabled or keyless means zero calls

- **WHEN** Tavily is disabled or no key is configured
- **THEN** zero Tavily requests are made and the analysis is marked `web_signals_enabled=False` in `meta`

#### Scenario: Tavily failure never breaks analysis

- **WHEN** a Tavily request fails or times out
- **THEN** the failure is recorded in `meta`, Maps data is unaffected, and the pipeline continues

### Requirement: Researcher uses real data with fixture fallback

The system SHALL wire `researcher_node` to Places Search + Details (+ Tavily when enabled), returning fixture data only when no Google key is configured.

#### Scenario: Real pipeline with keys

- **WHEN** `GOOGLE_PLACES_API_KEY` is configured
- **THEN** `researcher_node` returns deduplicated competitors from Search enriched with Details, plus `reviews_by_place` built from real review texts

#### Scenario: No keys means fixtures

- **WHEN** no Google key is configured
- **THEN** `researcher_node` returns the current 2-competitor Palermo fixture set and marks the analysis `stub=True` in `meta`

#### Scenario: Competitor cap respected

- **WHEN** Search returns more places than `max_competitors`
- **THEN** at most `max_competitors` competitors are kept and Details is fetched only for those

### Requirement: Analyze endpoint runs the real pipeline

The system SHALL make `POST /api/analyze` execute the LangGraph pipeline and return its competitors, clusters, opportunities, draft, and meta instead of the empty stub.

#### Scenario: End-to-end analysis

- **WHEN** an authenticated client posts a valid `business_type` + `zone`
- **THEN** the response contains pipeline-produced competitors, clusters, opportunities, and a draft post with `meta.trace` listing the executed nodes

### Requirement: Cost and quota safeguards

The system SHALL keep all external calls capped, cached, and testable without real network access.

#### Scenario: No real calls in tests

- **WHEN** the test suite runs
- **THEN** zero billable requests are made (mocked HTTP transports only) and new settings have safe defaults (`tavily_enabled=False`)

#### Scenario: Quota errors are retried then surfaced

- **WHEN** Places or Tavily returns 429/5xx
- **THEN** the request is retried with exponential backoff (max 3 attempts) and a persistent failure is recorded in `meta` without crashing the analysis
