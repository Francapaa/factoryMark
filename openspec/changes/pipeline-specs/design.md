## Context

See proposal.md (Why). Current state per stage:

- **Analyst**: `backend/src/nlp/` implements TF-IDF embeddings, TF-IDF+KMeans clustering (`k = min(5, max(2, n//6))`, `random_state=42`), ES lexicon sentiment with 3-word negation window, `trend_by_month`, and `competitive_score` (50/25/15/10). Tested with 30 Río de la Plata reviews.
- **Strategist**: `backend/src/agents/strategist.py` — negative cluster (sentiment < −0.2, count ≥ 2) → opportunity; alta if count ≥ 5 else media; fallback baja opportunity when no gaps.
- **Creator**: `backend/src/publisher.py:build_draft` template + `brand_kits/ejemplo.json` (name, colors, tone, handle).
- **Publisher**: `agents/publisher.py` asserts draft stays `draft`; `POST /api/approve` flips draft→approved/rejected in-memory; `PUBLISH_ENABLED=False`.
- **Orchestration**: `backend/src/graph.py` LangGraph linear chain over `AgentState` (TypedDict + `trace` reducer); `run_analysis(business_name, business_type, zone, sales_channel)`; `meta.trace` proves execution; tests block `httpx`/`httpx2` to prove zero network.
- **Evaluation**: `eval/golden_set.json` (5 cases), `eval/run.py` structural runner with keyword-recall heuristic, `eval/rubric.md` human 1–5 scoring.

## Goals / Non-Goals

**Goals:**

- Pin the above as testable SHALL requirements so future work modifies specs, not vibes.
- Make every `project.md` deviation explicit and justified (frontend stack, NLP backend, template copy, activity default).

**Non-Goals:**

- No behavior changes, no refactors, no new features in this change.
- No decisions on Fase 3 items (real publishing, image generation, pricing intel, alerts) — only recorded as out of scope with the questions left for the owner.

## Decisions

- **Specs describe current behavior, not aspirations**: where code is thinner than `project.md` (e.g. template copy vs "copy + imagen con brand kit"), the spec pins the thin behavior and names the gap, instead of spec'ing unbuilt features.
- **One capability per pipeline stage** (plus orchestration + evaluation): mirrors `project.md` §4 numbering so anyone can trace vision → spec → code file in one hop.
- **Deviations recorded inside each spec** (not hidden): each spec has a "Deviation from project.md" note where applicable.
- **No `specs/` promotion yet**: per repo convention these live under the change until reviewed; archiving to `openspec/specs/` happens after owner approval.

## Risks / Trade-offs

- [Risk] Specs rot if code moves without updating them → Mitigation: tasks.md requires a code-vs-spec verification pass per capability before review.
- [Risk] Pinning thin behavior (template copy) looks like endorsing mediocrity → Mitigation: each such spec states the upgrade path (LLM copy / image gen) as a named future change, not a silent TODO.

## Open Questions (for the owner)

1. **Creator scope for the demo**: template copy is enough for the technical demo, but is LLM-generated copy required before showing it to the 5–10 shop owners (Fase 2)? Which provider/model and budget cap?
2. **Image generation**: `project.md` §4 promises copy + image. In or out for the demo? If in, which provider (DALL-E, open-source) and who pays per image?
3. **Real publishing**: stays Fase 3 (igate decision so far), or is a manual "copy-paste to Instagram" export button wanted for Fase 2 validation?
4. **Activity signal**: scoring reserves 10% for postings/week but no source exists until Phase-2 Apify. Accept 0 default (documented), or drop the term until the data exists?
5. **Frontend stack**: `project.md` §7 says Streamlit, built is Next.js. Confirm Next.js as the official decision (spec assumes yes)?
6. **NLP upgrade**: sentence-transformers + HDBSCAN before or after Fase-2 validation? Current TF-IDF baseline is specified as sufficient for the demo.
