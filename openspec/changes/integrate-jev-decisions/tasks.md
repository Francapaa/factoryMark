## 1. Gateway Jev + config

- [ ] 1.1 Agregar settings `jev_enabled`, `typesafe_api_key`, `jev_confidence_threshold=0.70`, `jev_cache_ttl_hours=168`, topes por corrida/mes en `backend/src/config.py` + `.env.example`
- [ ] 1.2 Crear `backend/src/jev/` (cliente `evaluate(state, questions)` con timeout 2s + 1 reintento, schemas Pydantic Choice/Score/Noul, caché disco 7d por hash, contador de presupuesto)
- [ ] 1.3 Tests de contrato offline con fixtures grabadas: fallback sin key, timeout → baseline, respuesta con tipo inválido → descarte

## 2. Strategist scoring con escalación

- [ ] 2.1 Integrar Score accionabilidad + Choice tipo_gap en `agents/strategist.py` detrás del flag, combinando en código con la regla actual
- [ ] 2.2 Aplicar umbral de confianza: `>= umbral` adopta Jev, `< umbral` usa regla y marca `escalation=rule-fallback` en trace
- [ ] 2.3 Tests: alta confianza adopta tipo, baja confianza conserva regla, doble corrida idéntica con misma entrada

## 3. Creator routing + guardrail

- [ ] 3.1 Integrar Choice de plantilla (catálogo cerrado de 3) en `agents/creator.py` detrás del flag
- [ ] 3.2 Integrar Nouls de riesgo (nombra competidor, inventa precio/horario) que marcan `needs_review=true` y frenan pase a LLM
- [ ] 3.3 Tests: plantilla del catálogo, bloqueo por guardrail, offline completo sin red

## 4. Eval judge + medición del spike

- [ ] 4.1 Agregar `--with-jev` a `eval/run.py` con columnas `jev_razonabilidad` / `jev_accionabilidad` + confidences, sin cambiar exit-code estructural
- [ ] 4.2 Correr golden set en 3 modos (reglas, Jev, Jev+umbral calibrado) y registrar acuerdo, latencia p50/p99 y costo estimado por caso
- [ ] 4.3 Decisión go/no-go documentada: si Jev no supera reglas en es-AR, queda solo el gateway desactivado
