## Purpose

Answers "¿cuál es tu local?" with a real Maps match before anything is saved: the cheapest possible Places usage (one cached Search call) with explicit failure instead of fabrication. Shared by onboarding and the researcher.

## ADDED Requirements

### Requirement: Resolve name plus zone to a single anchored candidate

The system SHALL expose `POST /api/businesses/resolve` accepting `{name, zone}` (both non-empty) and returning the top-1 Places match: `place_id`, name, formatted address, rating (nullable), opening-hours summary, one `photo_ref`, latitude/longitude, and a free Google Maps link. Auth required.

#### Scenario: Known shop resolves

- **WHEN** an authenticated user posts a matching name + zone
- **THEN** the response contains the anchor fields above with `place_id` non-empty, served from cache when fresh (no billable call, `cached=True` in meta)

#### Scenario: Missing input rejected

- **WHEN** name or zone is empty/absent
- **THEN** the API responds 422 stating both fields are required

#### Scenario: Unresolvable shop fails explicitly

- **WHEN** no Places result matches with keys configured
- **THEN** the API responds 404 stating the business was not found and suggesting to verify the name — no candidate is invented and nothing is saved

#### Scenario: Keyless resolve is unavailable, not faked

- **WHEN** no Google key is configured
- **THEN** the API responds 400 stating resolution requires configuration, rather than returning fixture shops as if real

### Requirement: Shop photo served through backend proxy

The system SHALL expose `GET /api/businesses/photo?photo_ref=…` streaming image bytes with the server-side Places key; the browser never receives the key and the endpoint accepts no arbitrary URLs.

#### Scenario: Photo loads on the confirm screen

- **WHEN** the frontend requests the photo with the `photo_ref` from a resolve response
- **THEN** it receives image bytes (cacheable) without any key in the request or response

#### Scenario: Arbitrary URLs rejected

- **WHEN** the photo endpoint receives anything other than an opaque `photo_ref`
- **THEN** it responds 400 and fetches nothing
