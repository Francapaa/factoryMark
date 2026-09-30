## Purpose

Gives the onboarded owner a home where every pipeline output lives: business summary, FODA, competition, video studio, publications. Replaces the raw analysis form as the `/app` landing while keeping analysis one click away.

## ADDED Requirements

### Requirement: Five-section dashboard for onboarded users

The system SHALL render `/app` as a dashboard with sections: business summary (saved shop + anchor snapshot), FODA matrix, competition, video studio entry, publications history. The analysis form remains reachable as "Nuevo análisis" reusing the saved business by default.

#### Scenario: Onboarded landing

- **WHEN** a user with a saved business opens `/app`
- **THEN** all five sections render (each with its own loading/empty/error sub-state) without requiring per-request business fields

#### Scenario: Non-onboarded redirect

- **WHEN** a user without a saved business opens `/app`
- **THEN** they are routed to onboarding instead of the dashboard

### Requirement: Honest states everywhere

The system SHALL distinguish loading, empty (no data yet), error (with retry), and disconnected-Instagram states per section, in Spanish, never showing mock data as real.

#### Scenario: No analysis yet

- **WHEN** a fresh business has no analysis run
- **THEN** FODA/competition sections show an empty state with a "Generar análisis" action, not placeholders

#### Scenario: Instagram disconnected

- **WHEN** no IG account is connected
- **THEN** publications and studio-publish actions show a connect prompt; local pipeline sections work fully
