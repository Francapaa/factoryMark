## Purpose

Renders validated scenes into MP4 without ever blocking the API: an isolated worker consumes a queue, caches by content hash, and stores results behind signed URLs. (Worker, queue, and storage are a future change; this spec fixes behavior and cost controls.)

## ADDED Requirements

### Requirement: Async execution off the API process

The system SHALL render videos on a dedicated worker fed by a job queue; API requests enqueue and return a job id, never wait for ffmpeg.

#### Scenario: Enqueue is instant

- **WHEN** a valid scene is submitted for render
- **THEN** the API responds immediately with a job id and the MP4 appears later via job status

### Requirement: Content-hash render cache

The system SHALL cache renders by hash of (template + scene JSON + photo bytes + audio bytes) and serve cache hits without re-rendering.

#### Scenario: Identical scene is free

- **WHEN** an already-rendered scene is submitted again byte-identical
- **THEN** the stored MP4 URL is returned with zero render cost

### Requirement: Bounded cost per render

The system SHALL cap duration at 60 s and resolution at 1080×1920 in v1, and SHALL count renders per business per month toward the future cost ceiling.

#### Scenario: Oversized scene rejected before queueing

- **WHEN** a scene exceeds 60 s
- **THEN** it is rejected at validation time (see `scene-schema`), never queued

### Requirement: Private storage with signed URLs

The system SHALL store MP4s in object storage and serve them via expiring signed URLs; unapproved renders are retained only for a limited window (retention period set in the storage change).

#### Scenario: Expired link stops working

- **WHEN** a signed URL passes its expiry
- **THEN** it no longer serves the file
