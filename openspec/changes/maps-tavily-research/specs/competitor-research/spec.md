## Purpose

Gives the Researcher agent real, affordable competitor data anchored on the specific business and its sales channel — nearby rivals from Google Maps for local stores, web/social competitors via Tavily for online stores — replacing hardcoded fixtures while keeping local development and tests free of API costs.

## ADDED Requirements

### Requirement: Mandatory business anchor

The system SHALL require `business_name` on every analysis, resolve it to a Places anchor (top-1 result), and fail explicitly when it cannot be resolved — never silently falling back to fixtures when keys are configured.

#### Scenario: Missing business name rejected

- **WHEN** a client posts an analysis without `business_name` (empty or absent)
- **THEN** the API responds `422`/`400` with a message stating the business name is required

#### Scenario: Anchor resolved

- **WHEN** `business_name` plus `zone` match a Places result
- **THEN** the analysis records the anchor (`place_id`, name, formatted address, lat/lng) in `meta.anchor` and excludes it from the competitor list

#### Scenario: Unresolvable anchor fails explicitly

- **WHEN** no Places result matches in `local`/`mixto` mode with keys configured
- **THEN** the API responds `404` stating the business was not found and suggesting to verify the name — the pipeline does not run on fabricated competitors

### Requirement: Sales-channel branching

The system SHALL require `sales_channel` (`local | online | mixto`) and route research accordingly, tagging every competitor and signal with its source.

#### Scenario: Invalid channel rejected

- **WHEN** a client posts an unknown `sales_channel`
- **THEN** the API responds `422`/`400` listing the valid values

#### Scenario: Local mode searches by proximity

- **WHEN** `sales_channel` is `local`
- **THEN** competitors are searched with a `locationBias` circle centered on the anchor (radius `search_radius_m`, default 1000m), each carries `distance_m`, the list is sorted by proximity, and the anchor itself is excluded

#### Scenario: Online mode leads with web signals

- **WHEN** `sales_channel` is `online`
- **THEN** Tavily runs first (competitors selling the same product online, prices, delivery/marketplace presence, social profile links), Places runs best-effort, and web competitors carry `source="web"`

#### Scenario: Mixto merges both branches

- **WHEN** `sales_channel` is `mixto`
- **THEN** both branches run and results merge with `source` tags (`maps`|`web`), deduplicated by place_id/URL

### Requirement: Places Details enrichment

The system SHALL enrich each Maps competitor with real reviews, opening hours, and photos via the Places Details (Get Place) API, reusing the existing disk-cache, retry, and cap conventions.

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

The system SHALL collect off-Maps web signals via Tavily — mandatory for `online`/`mixto` (when a key is configured), optional enrichment for `local` — with per-analysis caps, caching, and failure isolation.

#### Scenario: Web signals attached for online

- **WHEN** `sales_channel` is `online`/`mixto` and `TAVILY_API_KEY` is configured
- **THEN** the analysis includes web competitors/signals (source URL + snippet + date each), capped at `tavily_max_queries` queries and `tavily_max_results` results each

#### Scenario: Local mode skips Tavily unless enabled

- **WHEN** `sales_channel` is `local` and Tavily enrichment is not enabled
- **THEN** zero Tavily requests are made and the analysis is marked `web_signals_enabled=False` in `meta`

#### Scenario: Tavily failure never breaks analysis

- **WHEN** a Tavily request fails or times out
- **THEN** the failure is recorded in `meta`, Maps data is unaffected, and the pipeline continues

### Requirement: Keyless fixture fallback

The system SHALL return fixture data only when no Google key is configured (local dev / CI), honestly flagged.

#### Scenario: No keys means fixtures

- **WHEN** no Google key is configured
- **THEN** `researcher_node` returns the 2-competitor Palermo fixture set and marks the analysis `stub=True` in `meta`

#### Scenario: Competitor cap respected

- **WHEN** Search returns more places than `max_competitors`
- **THEN** at most `max_competitors` competitors are kept and Details is fetched only for those

### Requirement: Analyze endpoint runs the real pipeline

The system SHALL make `POST /api/analyze` validate inputs, execute the LangGraph pipeline, and return its competitors, clusters, opportunities, draft, and meta instead of the empty stub; the frontend form SHALL call this endpoint with the three input fields instead of showing mock data.

#### Scenario: End-to-end analysis

- **WHEN** an authenticated client posts valid `business_name` + `business_type` + `zone` + `sales_channel`
- **THEN** the response contains pipeline-produced competitors, clusters, opportunities, and a draft post with `meta.trace` listing the executed nodes

#### Scenario: Frontend submits real requests

- **WHEN** the user fills business name, type, zone, and channel and submits
- **THEN** the form calls `POST /api/analyze` with a Bearer token and renders competitors, opportunities, and the draft from the response (loading and error states included)

### Requirement: Cost and quota safeguards

The system SHALL keep all external calls capped, cached, and testable without real network access.

#### Scenario: No real calls in tests

- **WHEN** the test suite runs
- **THEN** zero billable requests are made (mocked HTTP transports only) and new settings have safe defaults (`tavily_enabled=False` for local enrichment)

#### Scenario: Quota errors are retried then surfaced

- **WHEN** Places or Tavily returns 429/5xx
- **THEN** the request is retried with exponential backoff (max 3 attempts) and a persistent failure is recorded in `meta` without crashing the analysis

### Requirement: Phase 2 social metrics stay out of scope

The system SHALL NOT attempt social-media performance collection (post frequency, engagement, content mix) in this change; Tavily surfaces profile links only.

#### Scenario: Social links without metrics

- **WHEN** web signals include a competitor's Instagram/TikTok URL
- **THEN** the signal stores the URL and snippet context, and no request is made to scrape or measure that profile
