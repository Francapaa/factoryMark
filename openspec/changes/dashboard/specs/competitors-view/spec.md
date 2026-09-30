## Purpose

Shows who the rivals are at a glance: one card per competitor with the facts that matter (rating, distance, score, source), so the owner trusts the FODA underneath.

## ADDED Requirements

### Requirement: Rival cards with comparable facts

The system SHALL render one card per competitor: name, rating + review count, distance (local mode), competitive score, source tag (maps/web), address, and a Google Maps link.

#### Scenario: Competitors listed after analysis

- **WHEN** an analysis completes with N competitors
- **THEN** N cards render sorted by score descending, each with all fields above (missing optional fields show "—", never blank)

### Requirement: No-data view without fakes

The system SHALL show an explicit empty state when no competitors were found, offering to widen the radius or re-run — never fixture names.

#### Scenario: Empty competition

- **WHEN** the analysis returns zero competitors
- **THEN** the section explains why (radius, zone) with a retry action, not invented rivals
