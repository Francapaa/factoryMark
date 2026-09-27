## Purpose

Makes the "multi-agente con estado real" claim of `project.md` §3 concrete and verifiable: a LangGraph `StateGraph` chaining researcher → analyst → strategist → creator → publisher over a shared typed state, with proof of execution in every response. This is what separates the system from a single giant prompt.

## ADDED Requirements

### Requirement: Fixed five-node chain over shared state

The system SHALL run nodes in the fixed order researcher → analyst → strategist → creator → publisher over `AgentState` (business/zone inputs; competitors; `reviews_by_place`; clusters; scores; opportunities; draft; `trace` reducer).

#### Scenario: Node order is fixed and visible

- **WHEN** `run_analysis` completes
- **THEN** `meta.trace` equals `["researcher", "analyst", "strategist", "creator", "publisher"]` in that exact order

### Requirement: Single entrypoint with honest provenance

The system SHALL expose `run_analysis(business_name, business_type, zone, sales_channel="local")` returning the final state plus `meta` with `stub` provenance flag and `trace`.

#### Scenario: Fixture runs are flagged

- **WHEN** the researcher has no API keys and returns fixtures
- **THEN** the response carries `meta.stub=True`; keyed runs carry real provenance instead of silent mocks

### Requirement: Output compatible with the API contract

The system SHALL produce competitors, clusters, opportunities, draft, and meta coercible into `AnalyzeResponse` without loss.

#### Scenario: Contract validation

- **WHEN** a pipeline result is parsed as `AnalyzeResponse`
- **THEN** validation succeeds and the draft keeps its status

### Requirement: Graph contains exactly the five specified nodes

The system SHALL register precisely the nodes `researcher`, `analyst`, `strategist`, `creator`, `publisher` (no hidden side-channels between stages; every handoff goes through `AgentState`).

#### Scenario: Node inventory

- **WHEN** the compiled graph is inspected
- **THEN** its node set equals the five specified names

### Requirement: Offline-capable baseline

The system SHALL execute the full graph with all HTTP clients blocked (keyless fixture path), proving orchestration correctness independent of external APIs.

#### Scenario: Blocked-network run

- **WHEN** `httpx`/`httpx2` requests raise on any call
- **THEN** `run_analysis` still completes with a valid draft and full trace
