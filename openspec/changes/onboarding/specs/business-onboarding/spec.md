## Purpose

Makes onboarding optional to browse but mandatory to run agents: a short "decime tu local → confirmá que es este → guardado" flow gates the pipeline, so agents always work on a human-confirmed business and never on guesses.

## ADDED Requirements

### Requirement: Three-step onboarding flow

The system SHALL offer onboarding as: (1) form with shop name + location, (2) visual confirm screen ("¿Este es tu local?" with photo, address, rating, hours, Maps link, buttons Confirmar / No es este), (3) saved state unlocking the app.

#### Scenario: Happy path completes onboarding

- **WHEN** the user submits a name + location, sees the correct shop, and presses Confirmar
- **THEN** the business is saved, the app unlocks, and subsequent analyses default to the saved business without retyping

#### Scenario: Wrong match returns to form

- **WHEN** the user presses "No es este"
- **THEN** nothing is saved and the form is shown again preserving the typed values for correction

### Requirement: Optional to enter, mandatory to run agents

The system SHALL let authenticated users browse without completing onboarding, but SHALL refuse agent runs without a confirmed saved business.

#### Scenario: Analysis without onboarding is refused explicitly

- **WHEN** a user with no saved business calls `POST /api/analyze` without confirmed business data
- **THEN** the API responds 409 with code `onboarding_incompleto` and a message pointing to onboarding — the pipeline does not execute

#### Scenario: Completed onboarding unlocks analysis

- **WHEN** a user with a saved business calls `POST /api/analyze` (no per-request business fields needed)
- **THEN** the analysis runs anchored on the saved business

### Requirement: Re-onboarding replaces the single business

The system SHALL allow redoing onboarding at any time; confirming a new shop replaces the previous single row (one local per user until premium multi-local).

#### Scenario: Shop change

- **WHEN** an onboarded user completes onboarding again with a different shop
- **THEN** the saved business is replaced (upsert), history of the previous shop is not kept in v1
