## Why

`project2.md` §5 defines the video module (hybrid real-photos + motion graphics, templates + scene JSON), but nothing is specified or built: the Creator outputs text-only drafts, there is no scene contract, no template catalog, no asset pipeline, and no render path. Without the scene JSON contract fixed first, templates, upload UI, and render workers cannot be built independently. This change fixes the contract (executable Pydantic schema + validator) and specifies the surrounding capabilities.

## What Changes

- New executable scene schema: `backend/src/video/scene.py` (Pydantic models, closed vocabularies, validation rules from `project2.md` §5.4) with tests. No render, no upload endpoint, no new dependencies.
- Four new capability specs: `scene-schema` (implemented here), `asset-upload` (owner-provided music/voice via drag & drop — owner decision), `photo-qc` (pre-render photo checks + user guidance), `render-pipeline` (async worker, hash cache, object storage).
- Commits the previously untracked `project2.md` as the product vision document.

## Capabilities

### New Capabilities

- `scene-schema`: Validated scene JSON contract — 3-template catalog, closed motion/position vocabularies, length caps, photo/audio ownership checks, no-URL/HTML/code rule, default-template fallback. Implemented in this change.
- `asset-upload`: Owner uploads music/voice files (drag & drop); backend validates type/size/duration, stores per business; scenes reference `audio_id`. No TTS, no licensed library (owner decision).
- `photo-qc`: Pre-render checks (resolution, blur, light), auto-crop to vertical with centered subject, user warning instead of ugly output.
- `render-pipeline`: Async render queue on isolated worker (Remotion/FFmpeg), render cache by hash of (template + JSON + photos), object storage with signed URLs.

### Modified Capabilities

(none)

## Impact

- Code: new `backend/src/video/` package + `backend/tests/test_scene.py`. Pydantic only (already a dependency). Zero API cost, zero network.
- Docs: `project2.md` committed as vision; this change's specs become the build contract for templates, upload UI, and render worker (separate future changes).
- Explicitly out of scope: actual Remotion templates rendering, upload endpoint/UI, render worker, real publishing, generative (photographic) video.
