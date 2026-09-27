## 1. Proposal + design (this change)

- [x] 1.1 Write `proposal.md` (why: only Researcher spec'd; six gaps; docs-only, zero cost)
- [x] 1.2 Write `design.md` (current-state context, deviations, open questions for owner)

## 2. Specs (one capability per pipeline stage)

- [x] 2.1 `specs/analyst-nlp/spec.md` — TF-IDF+KMeans, lexicon sentiment, trend, 50/25/15/10 score, offline
- [x] 2.2 `specs/strategist-gaps/spec.md` — deterministic rules, cited evidence, alta/media/baja + honest fallback
- [x] 2.3 `specs/creator-draft/spec.md` — template draft from top opportunity + brand kit; LLM/image explicitly out
- [x] 2.4 `specs/publisher-hitl/spec.md` — draft stays pending, `/api/approve`, `PUBLISH_ENABLED=False`
- [x] 2.5 `specs/orchestration/spec.md` — LangGraph chain, `AgentState`, `run_analysis`, `meta.trace`, offline run
- [x] 2.6 `specs/evaluation/spec.md` — golden set, runner heuristic, human rubric, ≥3.5 bar

## 3. Verification (before owner review)

- [ ] 3.1 Code-vs-spec pass: re-read `backend/src/nlp/`, `agents/`, `publisher.py`, `graph.py`, `eval/` and fix any SHALL that the code does not actually satisfy
- [ ] 3.2 Cross-check against `competitor-research` spec: no contradictions on shared contracts (`Competitor`, `meta`, channels, cache conventions)
- [ ] 3.3 Run `uv run pytest` + confirm the suite still matches every testable scenario claimed

## 4. Owner review + archive

- [ ] 4.1 Owner answers the six open questions in `design.md` (LLM copy, image gen, real publishing, activity term, Next.js confirmation, NLP upgrade timing)
- [ ] 4.2 Apply review fixes, merge to `main`, archive specs to `openspec/specs/` per repo convention
