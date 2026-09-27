## Purpose

Implements the "Evaluación" pillar of `project.md` §3: measuring whether the agent's recommendations are reasonable, not just whether the demo runs. Defines the golden-set methodology — structural automation plus mandatory human judgment — and the bar for proceeding to Fase 2 validation.

## ADDED Requirements

### Requirement: Golden set of representative cases

The system SHALL maintain `eval/golden_set.json` with ≥ 5 cases, each carrying `id`, `business_name`, `business_type`, `zone`, `sales_channel`, `expected_insight`, and `min_competitors`.

#### Scenario: Case completeness

- **WHEN** the golden set is loaded
- **THEN** every case contains all required fields and at least 5 cases exist

### Requirement: Structural runner with keyword heuristic

The system SHALL provide `eval/run.py`, which runs each case through the real pipeline and reports per case: stub flag, competitor count vs minimum, opportunity count, keyword overlap/recall between `expected_insight` and produced evidence, and node trace. Keyword recall is a triage heuristic, NOT a quality verdict.

#### Scenario: Runner output is machine-checkable

- **WHEN** the runner executes
- **THEN** each case prints OK/FAIL on `min_competitors_ok`, and the process exits non-zero if any case fails structurally

#### Scenario: Keyless runs validate scaffolding only

- **WHEN** no API keys are configured
- **THEN** the runner executes on fixtures, flags `stub=True`, and its recall numbers measure plumbing — never insight quality

### Requirement: Human rubric as the quality verdict

The system SHALL define quality via `eval/rubric.md`: 1–5 razonabilidad (evidence-backed?) and 1–5 accionabilidad (concrete next action?), scored by a human comparing pipeline output against the analyst-grade expectation.

#### Scenario: Bar for Fase 2

- **WHEN** the golden set is scored by a human
- **THEN** an average ≥ 3.5 on both dimensions is required before showing the demo to real shop owners; below bar, the failing stages get spec'd fixes first

### Requirement: Real-data runs stay cheap and honest

The system SHALL run keyed evaluations against cached data where possible (7-day disk cache), with failures recorded per case without aborting the remaining cases.

#### Scenario: One bad case doesn't kill the run

- **WHEN** a case errors (unresolvable anchor, quota failure, etc.)
- **THEN** the error is printed for that case and the runner continues with the rest
