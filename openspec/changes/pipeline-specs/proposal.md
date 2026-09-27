## Why

`project.md` describes the vision (5-agent pipeline: Researcher → Analyst → Strategist → Creator → Publisher) but only the Researcher is specified (`competitor-research` in `maps-tavily-research`). The other four stages plus orchestration and evaluation exist as code but have no written contract: nobody — human or agent — can tell whether the built behavior matches the intended product, nor what is deliberately out of scope. Before iterating on the idea (real publishing, LLM copy, image generation, pricing intel) the current baseline must be pinned down in specs.

## What Changes

- Adds six new capabilities under `openspec/changes/pipeline-specs/specs/`, one per `project.md` §4 stage plus orchestration and evaluation: `analyst-nlp`, `strategist-gaps`, `creator-draft`, `publisher-hitl`, `orchestration`, `evaluation`.
- Each spec pins the CURRENT built behavior as SHALL requirements with scenarios (no code changes in this change — it is a specification baseline).
- Records deliberate deviations from `project.md`: Next.js frontend instead of Streamlit (§7), TF-IDF+KMeans instead of sentence-transformers+HDBSCAN (§6, with migration path), template copy instead of LLM copy (§4 Creator), `postings_per_week` defaulting to 0 until Phase-2 social data exists (§6 scoring).
- Records explicit non-goals carried over from `project.md` roadmap: real Meta/LinkedIn publishing, image generation, pricing intelligence, periodic alerts (all Fase 3).

## Capabilities

### New Capabilities

- `analyst-nlp`: Own NLP over competitor reviews — TF-IDF embeddings, KMeans topic clustering, lexicon sentiment with negation, monthly trend, and the documented 50/25/15/10 competitive score. No LLM, no network.
- `strategist-gaps`: Deterministic rules turning clusters into opportunities with cited evidence and alta/media/baja confidence. No LLM insight invention.
- `creator-draft`: Template draft post from the top opportunity + brand kit (name, tone, handle, hashtags). No LLM copy, no image generation.
- `publisher-hitl`: Drafts stay `draft` until human approval via `POST /api/approve`; `PUBLISH_ENABLED=False`, no real publishing.
- `orchestration`: LangGraph `StateGraph` researcher → analyst → strategist → creator → publisher over `AgentState`, `run_analysis` entrypoint, `meta.trace` proof of execution, output compatible with `AnalyzeResponse`.
- `evaluation`: Golden-set methodology — `eval/golden_set.json` cases, structural runner (`eval/run.py`, keyword-recall heuristic), human 1–5 rubric (`eval/rubric.md`), ≥3.5 bar to validate.

### Modified Capabilities

(none — `competitor-research` is untouched by this change)

## Impact

- Docs only: 1 proposal + 1 design + 6 specs + tasks. Zero code changes, zero new dependencies, zero API cost.
- Establishes the review baseline: any future change (LLM copy, image gen, real publishing, sentence-transformers) modifies these specs explicitly instead of drifting from `project.md` silently.
- Open product questions that this spec round surfaces are listed in `design.md` for the owner to decide.
