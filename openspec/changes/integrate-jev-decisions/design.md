## Context

Ver `proposal.md` para el porqué. Estado actual: `backend/src/graph.py` orquesta researcher → analyst → strategist → creator → publisher, todo local y determinístico; `agents/strategist.py` usa umbrales fijos (`-0.2`, `min 2`); `agents/creator.py` usa plantillas sin LLM; `eval/run.py` usa keyword-recall + rubric humano. Deps ya disponibles: `httpx`, `pydantic`, `pydantic-settings`. Restricción: presupuesto inicial $20, caché 7 días, pipeline debe seguir corriendo offline y early-access de TypeSafe sin SLA.

## Goals / Non-Goals

**Goals:**
- Capa System-One barata como primer decisor, LLM grande solo para copy final / baja confianza.
- Integración mínima, con flag, fallback idéntico al baseline y trazabilidad de probabilidades.
- Medir en `eval/` si Jev supera reglas en español rioplatense antes de expandir.

**Non-Goals:**
- Generar copy, imágenes o video con Jev (no genera strings).
- Cambiar API pública, frontend o schema.sql en este spike.
- Reemplazar el rubric humano por juez automático.

## Decisions

- **Cliente `src/jev/client.py` sobre `httpx` directo (no SDK pesado todavía):** una función `evaluate(state, questions)` que arma el payload TypeSafe (state + Choice/Score/Noul), 1 llamada por nodo, timeout corto (2s) + 1 reintento. Alternativa: SDK oficial / `system-one-adapter-python` — se evalúa si el spike rinde; hoy suma dependencia early-access sin beneficio.
- **Schemas Pydantic estrictos por pregunta:** cada Choice con `options` cerrada, cada Score con rango, cada Noul con umbral. Validación antes de usar; cualquier violación → fallback. Alternativa: aceptar strings libres — se rechaza porque reintroduce parsing/hallucination que Jev justamente elimina.
- **Preguntas atómicas compuestas en código:** en vez de "¿es buena oportunidad?", se pregunta `Score accionabilidad` + `Choice tipo_gap` + se combina con la fórmula determinística existente en código. Sigue la guía TypeSafe (atomic questions, composed in code) y evita context-rot.
- **State agregado, no verbatim:** al strategist se le pasa `{topic, count, avg_sentiment, 2 ejemplos truncados}` y al guardrail `{copy, oportunidad, brand}` — nunca reviews completas. Privacidad (project2.md §8) y menos input tokens ($0.042/MTok).
- **Escalación por `confidence` (default 0.70):** `>= umbral` adopta Jev; `< umbral` usa regla. Umbral en `Settings` (`jev_confidence_threshold`) para calibrar sin deploy de código. Alternativa: siempre-Jev — se rechaza hasta validar calibración en es-AR.
- **Caché disco 7d por hash + topes:** reutiliza `places_cache_ttl_hours=168` como patrón; `jev_cache_ttl_hours=168`, `jev_max_calls_per_run=3`, `jev_monthly_budget_per_business` en Settings. Sin Redis en el spike.
- **Eval como columna opt-in:** `eval/run.py --with-jev` agrega scores sin cambiar el exit-code estructural. El bar de Fase 2 (≥3.5 humano) no cambia.

## Risks / Trade-offs

- [Early-access sin SLA / pricing puede cambiar] → flag + fallback total; ningún test crítico requiere red; pin de versión de API y costo estimado por llamada en trace.
- [Calibración floja en español rioplatense] → umbral configurable + medición contra golden set; si `agreement < reglas`, el spike se declara no-go y queda solo el gateway.
- [Cardinalidad y latencia] → Choice con ≤ 8 opciones (lejos del tope 255); timeout 2s con fallback para no romper p99 del pipeline.
- [Fuga de PII en state] → solo agregados + ejemplos truncados; lista explícita de campos permitidos por llamada.
- [Drift de schemas TypeSafe] → validación estricta + tests de contrato con fixtures grabadas (VCR-style) sin red.

## Migration Plan

1. Merge con `JEV_ENABLED=false`: cero cambio observable; tests offline pasan.
2. Activar en staging con key de early-access + `--with-jev` en eval; calibrar umbral.
3. Rollback: unset del flag o quitar key → baseline puro, sin migración de datos (caché Jev es descartable).

## Open Questions

- ¿Umbral 0.70 es el punto correcto para es-AR o conviene 0.60/0.80 tras medir agreement en golden set?
- ¿Conviene el wrapper `system-one-adapter-python` para comparar Jev vs LLM con el mismo workflow en la fase de medición?
