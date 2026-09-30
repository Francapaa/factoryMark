## Purpose

Fixes the single contract every video feature builds on: what a valid scene looks like, which templates exist, and what is rejected. Implemented as executable Pydantic models in `backend/src/video/scene.py` so the contract is enforced, not just documented.

## ADDED Requirements

### Requirement: Three-template v1 catalog

The system SHALL offer exactly `producto_destacado_v1`, `oferta_promocion_v1`, and `horario_apertura_v1`, each with defaults (duration, allowed text positions); `TEMPLATES` is the single source of truth importable by validators and the future worker.

#### Scenario: Catalog inventory

- **WHEN** the catalog is inspected
- **THEN** it contains exactly the three v1 templates with durations 8–20s and 9:16 aspect

### Requirement: Closed vocabularies and length caps

The system SHALL accept only `motion` ∈ {zoom_in_suave, zoom_out_suave, pan_izquierda, pan_derecha, estatico}, `text_position` ∈ {top, center, bottom}, `aspect_ratio` = 9:16; `duration_seconds` 5–60; 1–8 scenes; per-scene `text` ≤ 80 chars; `cta` ≤ 40 chars; `caption` ≤ 220 chars; ≤ 5 hashtags each starting with `#`.

#### Scenario: Off-vocabulary rejected

- **WHEN** a scene uses `motion: "giro mortal"`
- **THEN** validation fails naming the `motion` field and its allowed values

#### Scenario: Over-length text rejected

- **WHEN** any text field exceeds its cap
- **THEN** validation fails naming the field and its cap

### Requirement: Ownership of referenced assets

The system SHALL accept only `photo_id`/`audio_id` values present in the caller-provided per-business id sets; unknown ids fail validation.

#### Scenario: Foreign photo rejected

- **WHEN** a scene references `photo_id` not owned by the business
- **THEN** validation fails and no render is attempted

### Requirement: No URLs, HTML, or code in any text field

The system SHALL reject text containing `http://`, `https://`, `<`, `>`, or `javascript:` (case-insensitive) in `text`, `cta`, `caption`, or hashtags.

#### Scenario: Injected markup rejected

- **WHEN** a caption contains a URL or HTML tag
- **THEN** validation fails identifying the offending field

### Requirement: Graceful fallback to default template

The system SHALL provide `default_scene()` (template `producto_destacado_v1`, silent, one static scene) for the pipeline to use after a failed retry.

#### Scenario: Fallback is always valid

- **WHEN** `default_scene()` output is validated
- **THEN** it passes with zero errors

### Requirement: The project2.md example validates

The system SHALL accept the `producto_destacado_v1` example from `project2.md` §5.3 (with owned ids) as valid.

#### Scenario: Golden example

- **WHEN** the §5.3 JSON is validated with its photo ids registered
- **THEN** it passes and preserves template, duration, scenes, cta, caption, and hashtags
