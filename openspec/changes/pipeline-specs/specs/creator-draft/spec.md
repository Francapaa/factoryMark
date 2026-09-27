## Purpose

Produces the concrete marketing artifact that covers the top opportunity — the "ejecutar" input of `project.md` §2. In the current baseline the copy is template-generated from the brand kit (name, tone, handle) plus fixed local hashtags; it is always a `draft`, never published. Implements `project.md` §4 stage [4] at template level (see deviation note).

## ADDED Requirements

### Requirement: Draft built from top opportunity plus brand kit

The system SHALL build a `DraftPost` via `build_draft(opportunity_title, brand)` where the copy names the business, references the opportunity, appends the handle, and notes the tone; hashtags default to `["#consumelocal", "#barrio"]`.

#### Scenario: Brand kit reflected in copy

- **WHEN** `build_draft` receives a brand with name, tone, and handle
- **THEN** the returned draft has status `draft`, non-empty `copy_text` containing the business name, and a non-empty hashtag list

#### Scenario: Missing brand fields degrade gracefully

- **WHEN** the brand dict lacks name, tone, or handle
- **THEN** defaults (`nuestro local`, `cercano`, empty handle) apply and a valid draft is still produced

### Requirement: Creator consumes the top-ranked opportunity

The system SHALL feed `opportunities[0]` (highest confidence, per strategist ordering) into the draft; with an empty list it falls back to a generic neighborhood topic.

#### Scenario: Top opportunity drives the draft

- **WHEN** the creator node runs on strategist output
- **THEN** the draft copy references the first opportunity's title

### Requirement: No LLM copy and no image generation in this baseline

The system SHALL NOT call any LLM or image model during draft creation.

#### Scenario: Draft creation is offline

- **WHEN** the creator runs with all network access blocked
- **THEN** it completes and returns a valid draft

### Deviation from project.md

§4 stage [4] prescribes "copy + imagen, con brand kit (colores, logo, tono)". Built is template copy only: no LLM copy, no image, colors/logo unused. Upgrade path (owner decision, see design.md open questions): LLM copy change (provider, model, per-draft cost cap, brand-kit prompt contract) and image-generation change (provider, payer, approval flow) as separate spec'd changes.
