## Purpose

Puts the owner in charge of music and voice (owner decision): audio reaches the system only as files the owner uploads (drag & drop), never via TTS or a licensed library. The backend validates, stores per business, and scenes reference uploads by id.

## ADDED Requirements

### Requirement: Upload validates type, size, and duration

The system SHALL accept audio uploads of type MP3/WAV, size ≤ 15 MB, duration ≤ 60 s, stored privately per business and addressable as `audio_id`. (Endpoint + UI are a future change; this spec fixes the contract.)

#### Scenario: Valid upload accepted

- **WHEN** an owner uploads a 30 s, 3 MB MP3
- **THEN** it is stored and an `audio_id` is returned for scene use

#### Scenario: Invalid upload rejected with reason

- **WHEN** the file is not MP3/WAV, exceeds 15 MB, or exceeds 60 s
- **THEN** the upload is rejected stating which limit failed, and nothing is stored

### Requirement: Rights confirmation at upload

The system SHALL require the owner to confirm they hold rights over the uploaded audio before storing it.

#### Scenario: No confirmation, no storage

- **WHEN** the rights checkbox is not confirmed
- **THEN** the upload is refused even if the file itself is valid

### Requirement: Scenes consume uploads by id only

The system SHALL resolve scene `audio_id` against the business's stored uploads; absent `audio_id` means a silent render (valid, not an error).

#### Scenario: Silent by default

- **WHEN** a scene carries no `audio_id`
- **THEN** validation passes and the render plan is silent
