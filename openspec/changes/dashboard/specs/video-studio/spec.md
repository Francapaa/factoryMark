## Purpose

Turns drafts into videos with the owner's real assets, simply: pick a draft, drop photos/audios, generate, preview, approve. Builds on the `scene-schema` contract and the `asset-upload`/`photo-qc` rules; no timeline editor in v1.

## ADDED Requirements

### Requirement: Draft-to-video flow in four steps

The system SHALL offer: (1) select an approved-or-draft post, (2) attach owner photos/audios via drag & drop (validated per `asset-upload`/`photo-qc`), (3) generate the scene (LLM fills the validated `scene-schema`), (4) render-job status → preview → approve.

#### Scenario: Happy path produces a preview

- **WHEN** a draft with attached owned assets is submitted
- **THEN** a render job is enqueued, its status is pollable, and completion yields a previewable MP4 with approve/reject actions

#### Scenario: Invalid assets block before queueing

- **WHEN** attached files fail upload or QC rules
- **THEN** the errors name each file and reason, and nothing is queued

### Requirement: Scene generation respects the contract

The system SHALL generate only `scene-schema`-valid scenes referencing owned asset ids; validation failures retry once with the error as context, then fall back to `default_scene()` (per `scene-schema`).

#### Scenario: Invalid scene never renders

- **WHEN** generation yields an invalid scene twice
- **THEN** the default template renders instead of failing the job

### Requirement: No editor in v1

The system SHALL NOT offer a timeline/scene editor; customization happens through asset choice and regeneration.

#### Scenario: Scope guard

- **WHEN** the studio scope is reviewed
- **THEN** frame-level editing is explicitly absent, deferred to a future change
