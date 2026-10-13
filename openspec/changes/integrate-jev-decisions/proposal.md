## Why

FactoryMark hoy decide con reglas fijas locales (cero LLM) y el copy con plantillas. Cuando se active LLM para clasificar oportunidades y redactar, el costo en tokens se dispara. Jev (TypeSafe System One) devuelve decisiones estructuradas tipadas con probabilidades calibradas a ~1/10 del costo y 70-500ms, sin generar texto. Usarlo como primera capa de decisión y reservar el LLM grande solo para el copy final y casos de baja confianza reduce costo y latencia manteniendo calidad.

## What Changes

- Agrega un gateway `JevGateway` en backend que evalúa `state + preguntas tipadas` (Choice / Score / Noul) contra TypeSafe API, con fallback a reglas actuales si no hay key o falla la red.
- Strategist: scoring de oportunidad vía Jev (`Score` accionabilidad + `Choice` tipo de gap) con confidence calibrada; si `confidence < umbral`, se mantiene la regla determinística actual.
- Creator: selección de plantilla vía `Choice` (producto_destacado / oferta / horario) + guardrail vía `Noul` (¿nombra competidor? ¿inventa precio/horario?); solo lo aprobado pasa a generación de copy (plantilla hoy, LLM mañana).
- Eval: juez de triage vía Jev (`Score` razonabilidad/accionabilidad) como complemento al keyword-recall actual; el veredicto sigue siendo el rubric humano.
- Todo detrás de feature-flag `JEV_ENABLED` + caché y topes de costo por negocio, sin romper el pipeline offline actual.

## Capabilities

### New Capabilities

- `jev-decisions`: gateway System-One + 3 puntos de decisión (strategist scoring, creator routing/guardrail, eval judge) con escalación por confianza y fallback a reglas.

### Modified Capabilities

(none — los comportamientos de `strategist-gaps`, `creator-draft` y `evaluation` definidos en `pipeline-specs` no cambian por defecto; Jev es una vía opt-in con fallback idéntico al baseline.)

## Impact

- Backend: nuevo módulo `src/jev/` (cliente, schemas Pydantic, caché), toques mínimos en `agents/strategist.py`, `agents/creator.py`, `eval/run.py`. Sin cambios de API ni frontend en este spike.
- Deps: `httpx` + `pydantic` (ya presentes) + key `TYPESAFE_API_KEY`; nueva dependencia externa TypeSafe (early access, uptime no garantizado).
- Riesgos: vendor early-access, calibración a validar en español rioplatense, cardinalidad máx 255. Mitigación: fallback determinístico + flag + umbral de escalación.
