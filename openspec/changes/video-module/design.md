## Context

See proposal.md (Why). Current state: Creator produces text-only `DraftPost`; `brand_kits/*.json` hold name/colors/tone/handle; no video code, no scene concept, no upload path, disk-JSON cache only (no DB, no object storage). `project2.md` §§3–5, 8–9 are the parent vision; this change executes its "próximos pasos" #1–2 (template catalog + scene schema/validator).

## Goals / Non-Goals

**Goals:**

- Executable scene contract now (schema + validator + tests) so all later video work builds on a fixed target.
- Specs for the three surrounding capabilities with owner decisions baked in (user-uploaded audio, no TTS/library).
- Name-mapping decision recorded so code and docs stop diverging.

**Non-Goals:**

- No rendering, no upload endpoint/UI, no worker, no storage integration.
- No FODA expansion, no publishing, no metrics (separate changes).

## Decisions

- **Pydantic models as the schema** (not bare JSON Schema): same validation library as the API contracts, validator is importable by the future render worker and testable in the existing suite.
- **3-template catalog v1**: `producto_destacado_v1`, `oferta_promocion_v1`, `horario_apertura_v1` — the three named in `project2.md` §12. Each template declares its own defaults (duration, allowed positions); variety grows by adding templates, never model freedom.
- **Audio is owner-uploaded, always**: per owner decision, no TTS and no licensed music library. Scene carries optional `audio_id` (must belong to the business); absent → silent render. `music_mood` kept as an optional hint for future library support, never a render input today.
- **Validation is strict, recovery is graceful**: unknown template, foreign `photo_id`/`audio_id`, off-vocabulary motion, over-length text, or any URL/HTML/code → reject with field-level errors. Pipeline behavior on reject (one retry with error context, then default template) is spec'd here, implemented in the future Creator-video wiring.
- **Name mapping (applies going forward)**: Researcher→Investigador, Analyst+Strategist→Estratega (FODA), Creator→Creativo, Publisher→Publicador, orchestration→Pipeline. Existing code keeps English identifiers until the module they live in is next touched; new video code uses the Spanish product names in docs and user-facing strings.
- **`owner_id` required on the future data model**: `Negocio` and all child entities carry the owner's identity (repo already has Neon auth); no multi-tenancy code in this change.

## Risks / Trade-offs

- [Risk] Pydantic validation runs in API process (CPU-trivial) — fine; heavy render stays out, in the future worker.
- [Risk] Owner-uploaded audio may be copyrighted material → Mitigation: terms checkbox on upload ("tenés derechos sobre este audio") + per-business private storage; spec'd in `asset-upload`, enforced in the future upload endpoint.
- [Risk] Template catalog too small feels repetitive → Mitigation: catalog is data; adding template #4 is a small spec'd change, no model or schema changes needed.

## Open Questions

- WhatsApp vs web delivery (project2.md §10.2): architectural fork (bot vs app), needed before Etapa 1 UI work. Still open — owner's call.
- Voiceover style guidance: with user uploads, do we give recording tips in-app (length, format)? Deferred to upload-UI change.
