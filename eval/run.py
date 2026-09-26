"""Golden-set runner: corre el pipeline real por caso y chequea estructura.

Sin API keys corre sobre fixtures (stub=True): valida el andamiaje, no la
calidad. Con keys (`backend/.env`) corre datos reales y el match de
`expected_insight` es un heurístico por palabras clave — la puntuación
1-5 de `rubric.md` (razonabilidad + accionabilidad) la pone un humano.

Uso desde backend/:  uv run python ../../eval/run.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parent.parent / "backend" / "src"
EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_SRC))

from graph import run_analysis  # noqa: E402

_STOPWORDS = {
    "de", "la", "el", "en", "que", "los", "las", "un", "una", "por",
    "con", "para", "como", "del", "al", "se", "su", "sus", "más", "muy",
    "sin", "nos", "nosotros", "podemos", "puede", "esto", "esta", "este",
}


def _keywords(text: str) -> set[str]:
    words = set(re.findall(r"[a-záéíóúñü]+", text.lower()))
    return {w for w in words if w not in _STOPWORDS and len(w) > 3}


def score_case(case: dict, result: dict) -> dict:
    opps = result.get("opportunities", [])
    evidence = " ".join(o.get("title", "") + " " + o.get("evidence", "") for o in opps)
    expected = _keywords(case.get("expected_insight", ""))
    found = _keywords(evidence)
    overlap = expected & found
    return {
        "id": case["id"],
        "stub": result.get("meta", {}).get("stub"),
        "n_competitors": len(result.get("competitors", [])),
        "min_competitors_ok": len(result.get("competitors", [])) >= case.get("min_competitors", 1),
        "n_opportunities": len(opps),
        "keyword_overlap": sorted(overlap),
        "keyword_recall": round(len(overlap) / max(1, len(expected)), 2),
        "trace": result.get("meta", {}).get("trace", []),
    }


def main() -> int:
    cases = json.loads((EVAL_DIR / "golden_set.json").read_text(encoding="utf-8"))
    print(f"{len(cases)} casos — rubric: eval/rubric.md (humano puntúa 1-5)\n")
    failures = 0
    for case in cases:
        try:
            result = run_analysis(
                case.get("business_name", "Negocio Ejemplo"),
                case["business_type"],
                case["zone"],
                case.get("sales_channel", "local"),
            )
        except Exception as exc:  # 404 ancla, 400 config, etc.
            print(f"[{case['id']}] ERROR: {exc}")
            failures += 1
            continue
        s = score_case(case, result)
        status = "OK " if s["min_competitors_ok"] else "FAIL"
        if not s["min_competitors_ok"]:
            failures += 1
        print(
            f"[{s['id']}] {status} stub={s['stub']} "
            f"competitors={s['n_competitors']} opps={s['n_opportunities']} "
            f"recall={s['keyword_recall']} overlap={s['keyword_overlap']}"
        )
    print(f"\n{len(cases) - failures}/{len(cases)} casos con estructura válida.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
