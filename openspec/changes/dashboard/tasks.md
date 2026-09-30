## 1. Specs (this change — project owner writes, no code)

- [x] 1.1 `proposal.md` — dashboard as product surface, Instagram staged for Meta review realities
- [x] 1.2 `design.md` — Instagram-Login flavor, connect-before-publish, own-reviews F/D, simple studio, history-without-metrics
- [x] 1.3 `specs/dashboard-overview/spec.md` — 5 sections, honest states, onboarding gate
- [x] 1.4 `specs/instagram-connect/spec.md` — OAuth, encrypted tokens, health, v1 profile-only, App Review milestone
- [x] 1.5 `specs/foda-matrix/spec.md` — F/D from own reviews, A from rival movement, honest empty quadrants
- [x] 1.6 `specs/competitors-view/spec.md` — rival cards, ordering, no-data view
- [x] 1.7 `specs/video-studio/spec.md` — 4-step flow, contract-respecting generation, no editor
- [x] 1.8 `specs/publication-history/spec.md` — Post lifecycle, history list, metrics off in v1

## 2. Implementation (other agents write the code, suggested order)

- [ ] 2.1 Dashboard shell: `/app` 5-section layout reusing saved business + existing `AnalyzeResult` types
- [ ] 2.2 `Post` persistence + history list (states, transitions, audit of rejected)
- [ ] 2.3 Competitors view + FODA matrix UI backed by existing pipeline output
- [ ] 2.4 Strategist expansion: own-review F/D clusters + threat rules (1 extra cached Details call)
- [ ] 2.5 Video studio: draft select + drag & drop uploads + scene generation + job-status polling
- [ ] 2.6 Instagram connect: OAuth (Instagram Login), encrypted token storage, health states, profile read
- [ ] 2.7 Publish + metrics milestones only after App Review approval (separate changes)
- [ ] 2.8 Full suites green (backend `uv run pytest`, frontend `pnpm lint && build`), zero real external calls in tests

## 3. Owner review + merge

- [ ] 3.1 Owner reviews this change
- [ ] 3.2 Merge to `main` only on explicit owner approval
