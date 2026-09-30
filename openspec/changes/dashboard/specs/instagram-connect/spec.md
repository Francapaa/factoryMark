## Purpose

Connects the owner's Instagram via the simple flavor ("entrá con tu Instagram", no Facebook Page needed), stores tokens safely, and stages capabilities so the product delivers value before Meta's App Review completes. Publishing stays gated until approval.

## ADDED Requirements

### Requirement: Instagram-Login OAuth flow

The system SHALL implement Business Login for Instagram against `graph.instagram.com` requesting `instagram_business_basic` (v1; publish permission added only with the publish milestone), exchanging the code server-side and never exposing secrets to the browser.

#### Scenario: Successful connect

- **WHEN** an owner completes the Instagram OAuth flow with a professional account
- **THEN** the backend stores the tokens and the dashboard shows the connected username with a disconnect option

#### Scenario: Personal account blocked with guidance

- **WHEN** the account is not professional
- **THEN** the UI explains the one-tap professional switch with a deep link instead of failing cryptically

### Requirement: Encrypted token storage with refresh and health

The system SHALL store IG tokens encrypted at rest per business, refresh them before expiry, and surface token health (valid / expired-needs-reconnect) on dashboard load — never failing silently.

#### Scenario: Expired token surfaces re-connect

- **WHEN** a stored token is expired or revoked
- **THEN** the dashboard shows a re-connect state and publish actions are disabled until reconnection

### Requirement: v1 reads profile only; publish gated on App Review

The system SHALL, in v1, read only the professional profile (username, counts) and SHALL NOT attempt publishing until Advanced Access is approved; UI publish actions remain hidden/disabled with an honest "próximamente" state.

#### Scenario: No premature publishing

- **WHEN** App Review is not yet approved
- **THEN** zero calls to container/publish endpoints occur and the UI offers copy/export of drafts instead

### Requirement: App Review tracked as an explicit milestone

The system SHALL treat Meta App Review (Business Verification, permission justifications, screencast of the real flow, testable build) as a gated milestone documented with a submission checklist, not as background paperwork.

#### Scenario: Submission readiness

- **WHEN** the publish milestone starts
- **THEN** a testable build, screencast, and per-permission justifications exist per the Meta checklist
