## 1. Specs (this change)

- [x] 1.1 `proposal.md` — scene contract first; templates/upload/render build on it
- [x] 1.2 `design.md` — Pydantic schema, 3-template catalog, owner-uploaded audio, name mapping, `owner_id`
- [x] 1.3 `specs/scene-schema/spec.md` — contract (implemented below)
- [x] 1.4 `specs/asset-upload/spec.md` — owner drag & drop audio, rights checkbox (contract only)
- [x] 1.5 `specs/photo-qc/spec.md` — checks, auto-crop, user guidance (contract only)
- [x] 1.6 `specs/render-pipeline/spec.md` — async worker, hash cache, signed URLs (contract only)

## 2. Implementation (this change: schema only)

- [x] 2.1 `backend/src/video/scene.py` — Pydantic models, `TEMPLATES` catalog (3 v1), closed vocabularies, caps, ownership + no-code validation, `default_scene()`
- [x] 2.2 `backend/tests/test_scene.py` — golden §5.3 example, each rejection rule, fallback validity, zero network
- [ ] 2.3 Commit `project2.md` (untracked vision doc) in this branch
- [x] 2.4 Full suite green (`uv run pytest` 67 passed, `ruff check` clean)

## 3. Owner review + merge

- [ ] 3.1 Owner reviews specs (open: WhatsApp vs web; recording tips in upload UI)
- [ ] 3.2 Merge to `main`; follow-up changes (templates render, upload endpoint/UI, worker) reference these specs
