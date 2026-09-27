## Purpose

Turns Analyst output into concrete, evidenced opportunities a shop owner can act on — the "decidir" step of `project.md` §2 (`detectar → decidir → ejecutar`). Rules are deterministic so every opportunity is traceable to data; no LLM invents insights. Implements `project.md` §4 stage [3].

## ADDED Requirements

### Requirement: Negative clusters become opportunities with cited evidence

The system SHALL convert every cluster with `avg_sentiment < −0.2` and `count >= 2` into an opportunity whose title names the topic and whose evidence cites the mention count, the sentiment value, and up to 2 verbatim examples.

#### Scenario: Rival pain becomes an opportunity

- **WHEN** a cluster `{"topic": "espera, lento", "count": 6, "avg_sentiment": −0.45, ...}` is processed
- **THEN** one opportunity is produced with confidence `alta`, title containing the topic, and evidence containing `6`, `−0.45`, and example texts

#### Scenario: Thin clusters are ignored

- **WHEN** a negative cluster has fewer than 2 mentions
- **THEN** no opportunity is produced from it (noise, not signal)

### Requirement: Confidence reflects evidence volume

The system SHALL assign `alta` to opportunities with count ≥ 5, `media` otherwise (negative clusters only; see fallback below).

#### Scenario: Confidence ordering

- **WHEN** multiple opportunities exist
- **THEN** they are sorted `alta` first, `media` next, `baja` last

### Requirement: Honest fallback when no gaps exist

The system SHALL return a single `baja`-confidence opportunity stating no clear gaps were found, rather than an empty list or a fabricated one.

#### Scenario: No negative clusters

- **WHEN** all clusters are neutral or positive
- **THEN** the result is exactly one opportunity titled about no clear gaps with confidence `baja`

### Requirement: No LLM in Strategist

The system SHALL derive opportunities from cluster data only, with fixed thresholds (`_NEGATIVE_THRESHOLD = −0.2`, `_MIN_COUNT = 2`) defined in code.

#### Scenario: Same input, same opportunities

- **WHEN** the strategist runs twice on identical clusters
- **THEN** outputs are identical (pure function of the input)
