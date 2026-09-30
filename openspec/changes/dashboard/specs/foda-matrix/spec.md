## Purpose

Completes the Strategist into a real FODA: keeps existing Opportunities, adds own-shop Fortalezas/Debilidades from the owner's reviews, and Amenazas from competitor movement — every quadrant backed by cited evidence with confidence, never generic advice.

## ADDED Requirements

### Requirement: Fortalezas from own positive clusters

The system SHALL cluster the saved anchor's own reviews (1 extra cached Details call per analysis) and surface positive clusters (sentiment > 0.2, count ≥ 2) as Fortalezas with cited examples.

#### Scenario: Praised topic becomes Fortaleza

- **WHEN** own reviews cluster positively around a topic with ≥ 2 mentions
- **THEN** a Fortaleza cites the topic, count, sentiment, and up to 2 verbatim examples

### Requirement: Debilidades from own negative clusters

The system SHALL surface own negative clusters (same thresholds as rival gaps) as Debilidades, framed as fixable items, never hidden.

#### Scenario: Own complaint is shown honestly

- **WHEN** own reviews cluster negatively with ≥ 2 mentions
- **THEN** a Debilidad cites the evidence exactly like an opportunity would

### Requirement: Amenazas from competitor movement

The system SHALL derive Amenazas from rival signals: competitors outscoring the shop, growing negative-cluster volume about topics the shop shares, or new high-rated entrants — each citing the underlying numbers.

#### Scenario: Stronger rival is a threat

- **WHEN** a competitor's score exceeds the shop's by a documented margin
- **THEN** an Amenaza names the rival and cites both scores

### Requirement: Low-evidence quadrants stay honest

The system SHALL render thin-evidence quadrants with their confidence and counts visible, stating data scarcity instead of inventing content.

#### Scenario: Empty quadrant

- **WHEN** a quadrant has no qualifying evidence
- **THEN** it shows an honest empty state ("aún sin datos suficientes"), never filler advice
