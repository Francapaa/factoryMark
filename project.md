# Agente de Inteligencia Competitiva con Capacidad de Acción

## 1. Resumen

Sistema multi-agente que, dado un negocio (rubro + zona), investiga a su competencia local, analiza señales públicas (reviews, ratings, actividad, precios), detecta oportunidades competitivas concretas y **genera y ejecuta una acción** para aprovecharlas (por ejemplo, un post para redes sociales listo para publicar).

No es un chatbot que responde preguntas sobre la competencia: es un agente que investiga, razona, decide y **actúa** con aprobación humana en el paso final.

## 2. Problema que resuelve

Un comercio o restaurante chico no tiene tiempo ni expertise para:
- Monitorear qué hace su competencia en la zona
- Extraer insights reales de reviews (propias y ajenas)
- Traducir esos insights en una acción concreta de marketing

Este agente automatiza ese ciclo completo: **detectar → decidir → ejecutar**.

## 3. Por qué no es "otro wrapper de chat"

La mayoría de los proyectos de "agentes IA" son un prompt + una llamada a la API. Este proyecto evita eso mediante:

- **Multi-agente con estado real**: cada etapa toma decisiones basadas en el output de la anterior (no es un solo prompt gigante).
- **NLP propio, no delegado**: embeddings + clustering para agrupar temas en reviews, en vez de pedirle al LLM que "adivine" los temas.
- **Tools con efectos reales**: el agente no solo lee datos, también escribe/publica contenido vía API — esto es lo que lo convierte en un agente "de acción" y no solo de research.
- **Human-in-the-loop**: el contenido generado queda listo para aprobar antes de publicarse, como referencia de patrón de producto real (inspirado en herramientas como [The Agentcy](https://theagentcy.app/)).
- **Evaluación**: se arma un set de casos de prueba para medir si las recomendaciones del agente son razonables, no solo "funciona en la demo".

## 4. Arquitectura (pipeline de agentes)

```
Input del usuario: tipo de negocio + zona/ubicación
   │
   ▼
[1] Researcher
   → Busca competidores vía Google Places API
   → Deduplica, maneja rate limits y errores
   │
   ▼
[2] Analyst
   → Extrae reviews de cada competidor
   → Sentiment analysis + clustering de temas (NLP propio: 
     sentence-transformers + k-means/HDBSCAN)
   → Calcula scoring competitivo (rating ponderado por 
     cantidad de reviews + recencia + actividad)
   │
   ▼
[3] Strategist
   → Cruza los datos y detecta gaps/oportunidades concretas
     (ej: "ningún competidor promociona el horario de tarde")
   │
   ▼
[4] Creator
   → Genera el contenido concreto para cubrir el gap
     (copy + imagen, con brand kit del negocio: colores, 
     logo, tono)
   │
   ▼
[5] Publisher
   → Deja el post listo para aprobar, o lo publica/programa
     directo vía API (Meta Graph API / LinkedIn API)
   → Acción con efecto real en el mundo, no solo texto
```

## 5. Fuentes de datos (legales y viables)

| Fuente | Uso | Vía |
|---|---|---|
| Google Places API | Competidores, ratings, horarios, fotos, reviews | API oficial |
| Reviews de Google | Sentiment, temas recurrentes, tendencia temporal | NLP propio sobre datos de la API |
| Instagram/redes | Frecuencia de posteo, tipo de contenido | Fase 2, vía API de terceros paga (Apify/Phantombuster) — nunca scraping directo, por ToS |

## 6. Componente NLP (lo que se construye, no se delega al LLM)

- **Clustering de reviews**: embeddings (sentence-transformers) + k-means/HDBSCAN para agrupar quejas/elogios recurrentes sin depender de que el LLM "invente" categorías.
- **Sentiment temporal**: no una foto fija, sino tendencia (¿mejoró o empeoró en los últimos meses?).
- **Scoring competitivo**: fórmula propia (rating + volumen de reviews + recencia + actividad), con decisiones de diseño documentadas.

## 7. Stack propuesto

- **Orquestación**: LangGraph o CrewAI
- **NLP**: sentence-transformers + clustering (propio) / LLM (Claude o GPT) para generación de copy e insights en lenguaje natural
- **Backend**: Python + FastAPI
- **Publicación**: Meta Graph API (Instagram), LinkedIn API — con OAuth y aprobación humana antes de publicar
- **Frontend demo**: Streamlit (para la demo técnica; se puede migrar después)

## 8. Alcance de la demo técnica (MVP)

Para la demo, el foco está en mostrar el patrón completo funcionando, aunque el alcance de datos sea acotado:

- Researcher + Analyst + Strategist funcionando sobre datos reales de Google Places
- Creator generando una pieza de contenido concreta a partir de un insight detectado
- Publisher **simulado o real** (según tiempo disponible): deja el post listo para aprobar; si da el tiempo, integración real con Instagram/LinkedIn
- Set básico de evaluación: casos de prueba donde se compara el insight del agente contra lo que diría un analista humano

## 9. Roadmap por fases

**Fase 1 — Demo técnica (actual)**
MVP con el pipeline completo, foco en mostrar ingeniería real: multi-agente con estado, NLP propio, tool use con efectos, evaluación.

**Fase 2 — Validación de demanda**
Mostrar la demo a 5–10 dueños de comercios/restaurantes reales y medir interés real antes de invertir en producto.

**Fase 3 — Producto (si hay demanda validada)**
- Integración completa con Instagram/LinkedIn (publicación y programación real)
- Pricing intelligence (comparación de menús/precios)
- Alertas periódicas (monitoreo continuo de la competencia)
- Multi-negocio, planes pagos, etc.

## 10. Qué diferencia a este proyecto de un chatbot de research

| | Chatbot de research | Este agente |
|---|---|---|
| Input → Output | Pregunta → respuesta en texto | Datos → insight → **acción ejecutada** |
| Datos | El usuario pregunta, el LLM responde de memoria o con RAG | Pipeline propio de recolección + NLP propio |
| Resultado final | Texto para que el usuario actúe manualmente | Contenido generado y listo para publicar (o publicado) |
| Control humano | No aplica | Aprobación antes de la acción final (human-in-the-loop) |
