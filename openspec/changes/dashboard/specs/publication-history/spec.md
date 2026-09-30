## Purpose

Keeps every draft and publication visible with its state, so nothing the agent produced gets lost. Metrics are defined in the type but collection stays off until the insights permission + App Review land (explicit future version).

## ADDED Requirements

### Requirement: Post entity with full lifecycle

The system SHALL persist `Post` records: id, business, opportunity reference, state ∈ borrador | aprobado | programado | publicado | rechazado, copy, scene JSON, `media_url`, `external_id` (nullable until published).

#### Scenario: Lifecycle transitions

- **WHEN** a draft is approved, scheduled, published, or rejected
- **THEN** its state advances accordingly with timestamps, and rejected posts are kept (not deleted) for audit

### Requirement: History list with states

The system SHALL render the owner's posts newest-first with state badges, copy/media preview, and (when published) the external link; drafts offer approve/reject/schedule actions per state.

#### Scenario: History after activity

- **WHEN** the owner has drafts and published posts
- **THEN** both appear ordered with correct states and only valid actions per state

### Requirement: Metrics defined but not collected

The system SHALL include metric fields (alcance, interacciones, guardados, fecha de captura) in the type while NEVER calling insights endpoints in v1; the UI shows no metrics section.

#### Scenario: No insights calls in v1

- **WHEN** the v1 suite runs with network blocked except allowed hosts
- **THEN** zero insights-API calls occur
