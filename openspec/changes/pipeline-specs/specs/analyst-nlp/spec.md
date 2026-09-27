## Purpose

Gives the Analyst stage its own NLP over competitor review texts — topic clustering, sentiment, monthly trend, and a competitive score — built with local libraries only. No LLM invents categories; no network call is ever made. Implements `project.md` §6 with a lighter baseline (see deviation note).

## ADDED Requirements

### Requirement: TF-IDF text embeddings with swappable interface

The system SHALL vectorize review texts with TF-IDF (`max_features=512`) behind the `embed_texts(texts) -> list[list[float]]` interface, keeping the signature stable for a future sentence-transformers backend.

#### Scenario: Embedding shape

- **WHEN** `embed_texts` receives N non-empty texts
- **THEN** it returns N vectors of equal length > 0, and `[]` for empty input

### Requirement: KMeans topic clustering with automatic k

The system SHALL group review texts into topics with TF-IDF + KMeans (`k = min(5, max(2, n//6))`, `random_state=42`), labeling each cluster with its top-3 centroid terms and the first 3 member texts as examples, sorted by size descending.

#### Scenario: Complaints separate from praise

- **WHEN** `cluster_reviews` receives a mixed set of ≥ 6 Spanish reviews
- **THEN** it returns 2–5 clusters whose total count equals the input size, with at least one negative-average and one positive-average cluster

#### Scenario: Too few texts yield one cluster

- **WHEN** fewer than 6 valid texts are provided (after stripping empties)
- **THEN** a single `general` cluster is returned with the mean sentiment of the set

#### Scenario: Deterministic output

- **WHEN** the same texts are clustered twice
- **THEN** both runs return identical topics and counts (`random_state` fixed)

### Requirement: Lexicon sentiment with negation handling

The system SHALL score Spanish review texts in −1..1 using positive/negative word lists, flipping polarity when a negation (`no`, `ni`, `nunca`, `jamás`, `tampoco`, `sin`) appears in the previous 3 words.

#### Scenario: Polarity and negation

- **WHEN** scoring clearly positive, clearly negative, negated-positive, and empty texts
- **THEN** results are > 0.2, < −0.2, < 0, and exactly 0.0 respectively

### Requirement: Monthly sentiment trend

The system SHALL aggregate `(iso_date, text)` pairs into `{YYYY-MM: average sentiment}` via `trend_by_month`, skipping unparseable dates.

#### Scenario: Trend direction is visible

- **WHEN** older reviews are negative and recent ones positive
- **THEN** the earliest month scores lower than the latest month

### Requirement: Documented competitive score

The system SHALL score each competitor 0..1 as `0.50·rating/5 + 0.25·log10(volume)/3 + 0.15·recency + 0.10·activity`, where recency decays linearly from 1 (0 days) to 0 (365 days) and activity saturates at 7 postings/week.

#### Scenario: Better competitor scores higher

- **WHEN** a high-rating, high-volume, recent, active competitor is compared with a low-rating, low-volume, stale, inactive one
- **THEN** the first score is strictly greater, both within 0..1

#### Scenario: Missing data degrades to zero, never crashes

- **WHEN** rating, date, or activity are missing/invalid
- **THEN** that term contributes 0 and `competitive_score(None, 0, None, 0)` returns exactly 0.0

#### Scenario: Activity defaults to zero without social data

- **WHEN** no Phase-2 social source exists for a competitor
- **THEN** `postings_per_week` is 0.0 and the activity term contributes 0 (documented, not hidden)

### Requirement: Zero network and zero LLM in Analyst

The system SHALL run the entire Analyst computation with local libraries only.

#### Scenario: Suite runs offline

- **WHEN** the Analyst tests execute with HTTP clients blocked
- **THEN** all tests pass with zero outbound requests

### Deviation from project.md

§6 prescribes sentence-transformers + k-means/HDBSCAN. Built is TF-IDF + KMeans (no torch dependency, instant tests, sufficient signal for ≤ 50 short reviews). Upgrade path: replace `embed_texts` internals with a multilingual sentence-transformer and KMeans with HDBSCAN as a named future change; the `ReviewCluster` contract does not change.
