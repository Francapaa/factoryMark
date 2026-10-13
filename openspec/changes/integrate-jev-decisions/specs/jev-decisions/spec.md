## Purpose

Provee decisiones estructuradas baratas y rápidas (System-One) como primera capa del pipeline, reservando el LLM grande solo para copy final y casos de baja confianza, sin romper el baseline offline determinístico.

## ADDED Requirements

### Requirement: Gateway Jev opt-in con fallback determinístico

The system SHALL exponer una vía Jev desactivada por defecto (`JEV_ENABLED=false`) que, cuando está activada y hay key, evalúa preguntas tipadas contra TypeSafe API y ante cualquier fallo (sin key, timeout, error de red, respuesta inválida) devuelve el resultado del baseline determinístico actual sin abortar el pipeline.

#### Scenario: Desactivado por defecto es baseline puro

- **WHEN** `JEV_ENABLED` no está seteado o es `false`
- **THEN** strategist, creator y eval se comportan exactamente como hoy (reglas fijas + plantillas + keyword-recall), sin ningún request saliente a TypeSafe

#### Scenario: Fallo de Jev no rompe el pipeline

- **WHEN** Jev está activado pero la API responde error o timeout
- **THEN** el nodo registra `jev_fallback=true` en el trace y devuelve el resultado del baseline, y el pipeline completa de punta a punta

### Requirement: Preguntas atómicas en paralelo con salidas tipadas

The system SHALL enviar en una sola llamada el `state` (clusters, oportunidad, copy) más un lote de preguntas atómicas (Choice / Score / Noul) y validar que cada respuesta respete su schema (opciones cerradas, rangos 0-1), descartando cualquier respuesta con error de tipo hacia fallback.

#### Scenario: Batch paralelo de strategist

- **WHEN** el strategist evalúa un cluster con 2 preguntas (Score accionabilidad + Choice tipo de gap)
- **THEN** ambas respuestas llegan en una sola llamada, cada una con valor tipado + distribución de probabilidades + confidence

#### Scenario: Respuesta con tipo inválido se descarta

- **WHEN** Jev devuelve un `Choice` fuera de la lista cerrada o un `Score` fuera de rango
- **THEN** esa respuesta se ignora, se marca fallback y se usa la regla determinística

### Requirement: Strategist scoring con escalación por confianza

The system SHALL puntuar cada cluster candidato vía Jev y solo aceptar el veredicto Jev cuando `confidence >= umbral` (default 0.70, configurable); bajo el umbral SHALL conservar la regla actual (`avg_sentiment < -0.2` y `count >= 2`, `alta` si `count >= 5`).

#### Scenario: Alta confianza adopta el tipo Jev

- **WHEN** un cluster `espera, count=6, sentiment=-0.45` recibe `Choice=dolor-rival` con `confidence=0.88`
- **THEN** la oportunidad resultante usa ese tipo y confidence `alta`, con evidencia que cita count, sentiment y hasta 2 ejemplos

#### Scenario: Baja confianza conserva la regla

- **WHEN** Jev devuelve `confidence=0.45` para el mismo cluster
- **THEN** el sistema ignora el tipo Jev y aplica la regla determinística actual, marcando `escalation=rule-fallback` en el trace

### Requirement: Creator routing de plantilla y guardrail de seguridad

The system SHALL elegir la plantilla de post vía `Choice` entre el catálogo cerrado (`producto_destacado_v1`, `oferta_promocion_v1`, `horario_apertura_v1`) y bloquear el pase a copy si algún `Noul` de riesgo supera su umbral (nombra competidor específico, inventa precio/horario no aportado por el dueño).

#### Scenario: Plantilla elegida del catálogo

- **WHEN** la top oportunidad es de horario de tarde y Jev elige `horario_apertura_v1` con alta confianza
- **THEN** el draft usa esa plantilla y el copy de plantilla actual, sin llamar a ningún LLM

#### Scenario: Guardrail bloquea copy riesgoso

- **WHEN** el `Noul` "el copy nombra o ataca a un competidor" supera 0.5 o el `Noul` "afirma precio/horario no verificado" supera 0.5
- **THEN** el draft se marca `needs_review=true` con motivo, no avanza a generación LLM, y queda en `borrador` para aprobación humana

### Requirement: Eval con juez Jev como triage, humano como veredicto

The system SHALL agregar al runner `eval/run.py` una columna opt-in `jev_score` (Score razonabilidad 0-1 y Score accionabilidad 0-1 por caso) que complementa el `keyword_recall` actual y nunca sustituye la puntuación humana 1-5 de `rubric.md`.

#### Scenario: Runner sin Jev no cambia

- **WHEN** se corre `eval/run.py` sin flag Jev
- **THEN** la salida es idéntica a la actual (OK/FAIL, recall, trace) sin columnas nuevas obligatorias

#### Scenario: Runner con Jev reporta scores por caso

- **WHEN** se corre con Jev activado
- **THEN** cada caso imprime además `jev_razonabilidad` y `jev_accionabilidad` con sus confidences, y el proceso sigue saliendo non-zero solo por fallos estructurales

### Requirement: Costos acotados, caché y observabilidad

The system SHALL cachear respuestas Jev por hash de (state + preguntas) con TTL 7 días como Places, aplicar topes (máx 1 llamada Jev por nodo por corrida, máx N llamadas por negocio por mes configurable), registrar latencia/costo estimado por llamada en el trace, y nunca enviar reviews verbatim con datos personales sino temas agregados.

#### Scenario: Segunda corrida usa caché

- **WHEN** se repite el mismo análisis dentro del TTL
- **THEN** no se emite ningún request a TypeSafe y el trace marca `jev_cached=true`

#### Scenario: Tope mensual corta a fallback

- **WHEN** un negocio supera su tope mensual de llamadas Jev
- **THEN** las llamadas restantes del mes devuelven baseline sin error y el trace marca `jev_budget_exceeded=true`
