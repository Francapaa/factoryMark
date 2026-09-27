## Purpose

Guarantees the human-in-the-loop promise of `project.md` §3: the agent prepares the action but a human approves it before anything happens in the real world. In the current baseline nothing is published anywhere — drafts wait as `draft` and flip to `approved`/`rejected` only through `POST /api/approve`. Implements `project.md` §4 stage [5] at mock level (see deviation note).

## ADDED Requirements

### Requirement: Pipeline output is always a pending draft

The system SHALL finish every analysis with the draft in `draft` status, asserting it before returning.

#### Scenario: Fresh analysis leaves draft pending

- **WHEN** the pipeline completes
- **THEN** `draft_post.status` is `draft` (never auto-approved, never published)

### Requirement: Explicit human approval endpoint

The system SHALL expose `POST /api/approve` accepting `{approved: bool}` (plus optional opportunity/brand context) and returning the draft with status `approved` or `rejected`.

#### Scenario: Approve and reject paths

- **WHEN** a client posts `{"approved": true}` (resp. `false`)
- **THEN** the response draft carries status `approved` (resp. `rejected`)

### Requirement: Real publishing disabled by flag

The system SHALL keep `PUBLISH_ENABLED = False`, and no code path SHALL contact Meta, LinkedIn, or any publishing API while the flag is off.

#### Scenario: No publish side effects

- **WHEN** the full test suite runs with network blocked
- **THEN** zero publishing calls occur and all publisher tests pass

### Deviation from project.md

§4 stage [5] and §7 prescribe leaving the post ready "o publicarlo/programarlo directo vía API (Meta Graph API / LinkedIn API)" with OAuth. Built is approve/reject bookkeeping only: no OAuth, no scheduling, no external calls. Upgrade path (Fase 3): real-publishing change specifying provider, OAuth flow, per-account token storage, scheduling semantics, and audit log — as a separate spec'd change.
