# FactoryMark — Plan de producto y arquitectura

> **Tu espía legal de la competencia, que además te escribe el marketing.**

Documento de diseño para evolucionar FactoryMark de demo técnica a producto usable. Cubre la visión, el alcance por etapas, la arquitectura, el módulo de video, la integración con redes, los riesgos y cómo validar cada paso con dueños de locales reales.

---

## 1. Visión

Un agente que, para un comercio de barrio, cierra este ciclo de punta a punta:

```
Investiga la zona → Detecta oportunidades (FODA) → Crea el contenido
        ↑                                                  ↓
   Itera con métricas ← Mide resultados ← Programa y publica (con aprobación)
```

El dueño sube fotos de sus productos, aprueba o rechaza, y el sistema se ocupa del resto.

### Qué nos diferencia

La mayoría de las herramientas (Canva, Buffer, Later, Meta) resuelven **diseñar y programar**. Ninguna decide **qué publicar según lo que hace la competencia cercana**. Ese es el diferencial y el que hay que proteger:

> El contenido nace de un dato real de la zona ("dos competidores tienen quejas por la demora", "nadie promociona la tarde"), no de una plantilla genérica.

### A quién le servimos

Cafés, restaurantes, barberías, panaderías y comercios chicos con presencia en Instagram y/o TikTok, sin tiempo ni equipo de marketing.

---

## 2. Principios de diseño

1. **Humano en el circuito.** Nada se publica sin aprobación explícita (al menos hasta que haya evidencia sólida de calidad).
2. **Determinismo antes que libertad.** El modelo decide *qué* comunicar; el código decide *cómo* se renderiza. Claude no ejecuta código libre en el servidor.
3. **Una red primero.** Cada integración cuesta semanas y mantenimiento. Se agrega la siguiente solo si la anterior demostró valor.
4. **Costos acotados.** Caché agresiva, límites por usuario, datos de ejemplo en desarrollo.
5. **Validar con personas reales antes de construir más.**

---

## 3. Alcance por etapas

| Etapa | Alcance | Pregunta que responde | Criterio de éxito |
|---|---|---|---|
| **0 — Demo técnica** *(actual)* | Competidores, reseñas, oportunidades, borrador de texto, aprobación | ¿Funciona el pipeline de punta a punta? | Corre completo con datos reales |
| **1 — Foto → post** | El dueño sube fotos; el sistema genera post (imagen o video corto por plantilla) con texto basado en la oportunidad detectada | ¿Aprueban y usan lo que se genera? | ≥ 60 % de borradores aprobados con cambios menores |
| **2 — Publicación** | Conexión con Instagram, programación, horario sugerido, siempre con aprobación | ¿Publican más seguido gracias a la herramienta? | Frecuencia de publicación sube vs. línea base |
| **3 — Métricas** | Lectura de métricas y reporte semanal simple (WhatsApp o mail) | ¿Les sirve saber qué funcionó? | El dueño abre el reporte y actúa sobre él |
| **4 — Iteración y expansión** | TikTok, aprendizaje sobre métricas propias, más plantillas de video | ¿Pagan por esto? | Conversión a plan pago |

**Regla:** no se empieza la etapa N+1 sin haber mostrado la etapa N a 5–10 dueños reales.

---

## 4. Arquitectura

### 4.1 Vista general

```
┌──────────────┐     ┌──────────────────────────────────────────────┐
│   Frontend   │────▶│                  Backend API                 │
│  (Next.js)   │     │                  (FastAPI)                   │
└──────────────┘     └───────┬──────────┬───────────┬───────────────┘
                             │          │           │
                    ┌────────▼───┐ ┌────▼─────┐ ┌───▼────────────┐
                    │ Investigador│ │ Estratega│ │  Creativo      │
                    │ (Maps, web) │ │  (FODA)  │ │ (copy + escena)│
                    └────────┬───┘ └────┬─────┘ └───┬────────────┘
                             │          │           │
                    ┌────────▼──────────▼───┐  ┌────▼─────────────┐
                    │  Caché + Base de datos │  │  Cola de render  │
                    │  (Postgres / Redis)    │  │  (worker)        │
                    └────────────────────────┘  └────┬─────────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │ Remotion / FFmpeg     │
                                          │ + almacenamiento (S3) │
                                          └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │  Publicador           │
                                          │  (Instagram → TikTok) │
                                          └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │  Recolector métricas  │
                                          └───────────────────────┘
```

### 4.2 Componentes

| Componente | Responsabilidad | Notas |
|---|---|---|
| **Investigador** | Busca competidores cercanos (Google Maps), reseñas, horarios, fotos; en modo online, menciones web | Caché 7 días, tope de consultas por usuario |
| **Estratega** | Agrupa temas de reseñas, arma el FODA, detecta huecos concretos | Reglas explícitas + LLM para clasificación; salida estructurada |
| **Creativo** | Redacta el copy y define la **escena** (JSON) a partir de la oportunidad, el brand kit y las fotos | El LLM devuelve JSON validado, no código |
| **Cola de render** | Ejecuta renders de video de forma asíncrona | CPU intensivo; aislado del API |
| **Publicador** | Publica o programa en cada red | Un adaptador por red, misma interfaz |
| **Recolector de métricas** | Trae alcance, interacciones, guardados, etc. | Frecuencia y campos dependen de lo que permita cada API |
| **Evaluación (`eval/`)** | Casos de prueba para medir calidad del FODA y del copy | Se corre en cada cambio de prompts |

### 4.3 Modelo de datos (mínimo)

```
Negocio        id, nombre, tipo, canal (local|online|mixto), ubicacion, brand_kit_id
BrandKit       id, colores, tono, logo, tipografia
Competidor     id, negocio_id, place_id, nombre, distancia, rating, ultima_actualizacion
Oportunidad    id, negocio_id, tipo, evidencia[], puntaje, creada_en
Post           id, negocio_id, oportunidad_id, estado, copy, escena_json, media_url
                 estado ∈ borrador | aprobado | programado | publicado | rechazado
Publicacion    id, post_id, red, programada_para, publicada_en, id_externo
Metrica        id, publicacion_id, capturada_en, alcance, interacciones, guardados, ...
```

---

## 5. Módulo de video

### 5.1 Qué es y qué no es

Claude **no genera video fotográfico**. Lo que sí es viable y suficiente para un comercio chico son **motion graphics por código**: movimiento suave sobre las fotos reales del local, texto animado, precios, ofertas, logo y transiciones al ritmo de una música.

Si en el futuro se quisiera animación generativa (modelos de video de terceros), sería un módulo aparte, opcional, con más costo y más tasa de fallos. No es parte del plan inicial.

### 5.2 Enfoque: plantillas + JSON de escena

**No** dejar que Claude escriba código de animación libre en cada post: es impredecible, falla seguido y ejecutar código generado en el servidor es un riesgo de seguridad.

En su lugar:

1. Nosotros mantenemos **5–10 plantillas** de video (Remotion) parametrizadas.
2. Claude devuelve **solo un JSON** describiendo la escena.
3. El backend **valida** el JSON contra un esquema y renderiza con la plantilla elegida.

Resultado: respeta el brand kit, casi nunca se rompe, y el costo por render es predecible. La variedad se logra agregando plantillas, no libertad al modelo.

### 5.3 Ejemplo de JSON de escena

```json
{
  "template": "producto_destacado_v1",
  "duration_seconds": 12,
  "aspect_ratio": "9:16",
  "music_mood": "calido_acustico",
  "scenes": [
    {
      "photo_id": "ph_001",
      "motion": "zoom_in_suave",
      "text": "Café de especialidad",
      "text_position": "bottom"
    },
    {
      "photo_id": "ph_004",
      "motion": "pan_izquierda",
      "text": "Abierto hasta las 21 h",
      "text_position": "center"
    }
  ],
  "cta": "Pasá esta tarde",
  "caption": "Mientras otros cierran temprano, nosotros seguimos acá. ☕",
  "hashtags": ["#cafedebarrio", "#sanjusto"]
}
```

### 5.4 Reglas de validación del JSON

- `template` debe existir en el catálogo.
- Todo `photo_id` debe pertenecer al negocio.
- `motion`, `text_position` y `music_mood` limitados a listas cerradas.
- Largo máximo de cada texto y de la duración total.
- Sin URLs, HTML ni código en ningún campo.
- Si falla la validación: se reintenta una vez con el error como contexto; si vuelve a fallar, se usa una plantilla por defecto.

### 5.5 Control de calidad de fotos

Las fotos de un local suelen ser malas. Antes de renderizar:

- Detectar baja resolución, desenfoque fuerte y poca luz.
- Recortar automáticamente al formato vertical con el sujeto centrado.
- Avisar al dueño ("esta foto está oscura, ¿subís otra?") en vez de generar algo feo.

### 5.6 Infraestructura de render

- Cola de trabajos con worker dedicado (el render es CPU intensivo y no debe bloquear el API).
- Opciones: worker propio o Remotion sobre AWS Lambda. **Verificar precios y límites actuales antes de decidir.**
- Cachear renders por hash de (plantilla + JSON + fotos).
- Guardar el resultado en almacenamiento de objetos y servir por URL firmada.

---

## 6. Integración con redes sociales

### 6.1 Estrategia

Un adaptador por red detrás de una interfaz común:

```
class Publicador:
    autenticar(negocio) -> credenciales
    subir_media(credenciales, archivo) -> media_id
    programar(credenciales, media_id, caption, fecha) -> publicacion_id
    obtener_metricas(credenciales, publicacion_id) -> Metricas
```

Orden sugerido: **Instagram primero**. TikTok recién en la etapa 4.

### 6.2 Advertencias importantes

- Las APIs de cada red tienen reglas propias, requisitos de tipo de cuenta y, en varios casos, **revisión o auditoría de la app** antes de permitir publicar.
- Estas políticas cambian con frecuencia. **Antes de diseñar en detalle, leer la documentación oficial vigente** de cada red (permisos, tipos de cuenta, límites de publicación, campos de métricas disponibles).
- Planear un tiempo de aprobación de permisos como parte del cronograma: no depende de nosotros.
- Guardar los tokens cifrados y con renovación automática.

### 6.3 Alternativa si la integración directa se complica

Usar un proveedor intermedio de publicación multi-red en lugar de integrar cada API. Evaluar costo, cobertura y dependencia antes de decidir.

---

## 7. Métricas e iteración

### 7.1 Realismo sobre los datos

Un comercio con pocos cientos de seguidores que publica 2–3 veces por semana genera **muy pocos datos**. Con ese volumen, conclusiones como "el mejor horario es el martes a las 19 h" son mayormente ruido.

### 7.2 Enfoque por capas

| Capa | Cuándo | Qué hace |
|---|---|---|
| **Reglas generales** | Desde el inicio | Horarios y formatos basados en buenas prácticas por rubro |
| **Reporte descriptivo** | Etapa 3 | "Este post tuvo más guardados que tu promedio" |
| **Comparación simple** | Con ≥ 15–20 publicaciones | Comparar formatos/temas dentro del mismo negocio |
| **Aprendizaje personalizado** | Solo con volumen suficiente | Ajustar horarios y temas con criterio estadístico honesto |

**No prometer** "el agente aprende de tus métricas" hasta que haya datos para sostenerlo. Mientras tanto, el reporte semanal ya aporta valor.

### 7.3 Métricas a seguir (sujetas a lo que exponga cada API)

Alcance, impresiones, interacciones, guardados, compartidos, clics al perfil, retención en video.

---

## 8. Seguridad, privacidad y legalidad

- **Aprobación humana obligatoria** antes de publicar. Guardar quién aprobó qué y cuándo.
- **Contenido sobre competidores:** el análisis usa información pública, pero el copy generado **no debe nombrar ni atacar** a un competidor específico. Regla dura en el prompt y validación posterior.
- **Afirmaciones verificables:** precios, horarios y promociones vienen de datos cargados por el dueño, no inventados por el modelo.
- **Términos de servicio:** revisar las condiciones de uso de Google Maps/Places y de cada red respecto de almacenamiento y reutilización de datos. Respetar los límites de caché permitidos.
- **Ejecución de código:** el modelo nunca produce código que se ejecute en el servidor. Solo JSON validado contra esquema.
- **Datos de clientes:** las reseñas pueden contener datos personales. No exponerlas tal cual; trabajar con temas agregados.
- **Credenciales:** cifradas en reposo, permisos mínimos, revocables por el dueño.
- **Marco local:** consultar requisitos de protección de datos personales aplicables en Argentina.

---

## 9. Costos

| Fuente de costo | Control |
|---|---|
| Consultas a Google Maps/Places | Caché 7 días, tope por usuario, datos de ejemplo en desarrollo |
| Llamadas al LLM | Prompts acotados, salida estructurada, reutilizar análisis del FODA entre posts |
| Render de video | Caché por hash, plantillas simples, duración máxima |
| Almacenamiento | Retención limitada de renders no aprobados |
| Métricas de redes (Apify u otros) | Solo en etapa 3+, evaluar si la API oficial alcanza |

Definir un **costo máximo por negocio por mes** y medirlo desde el primer usuario real.

---

## 10. Validación con usuarios reales

### 10.1 Plan (Etapa 1)

1. Elegir **5–10 locales** de la zona (San Justo y alrededores).
2. Correr el pipeline para cada uno y llevarles el resultado **por WhatsApp o impreso**.
3. Pedirles fotos reales de sus productos y generar 2–3 posts para cada uno.
4. Observar qué hacen: ¿aprueban?, ¿editan mucho?, ¿publican?

### 10.2 Preguntas clave

- ¿Qué parte te sirvió más: saber qué hace la competencia o recibir el post listo?
- ¿Publicarías esto? ¿Qué cambiarías?
- ¿Lo usarías todas las semanas?
- ¿Cuánto pagarías por mes? ¿Y si fuera la mitad de funciones?
- ¿Preferís recibirlo en una web o por WhatsApp?

### 10.3 Señales de que hay producto

- Publican lo generado sin pedir rehacerlo.
- Piden que se lo mandes la semana siguiente sin que se lo ofrezcas.
- Mencionan un precio antes de que preguntes.

### 10.4 Señales de alerta

- "Está lindo" pero no publican.
- Solo les interesa una parte (probablemente ese es el producto real).
- Prefieren hacerlo ellos mismos con Canva.

---

## 11. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Aprobación de apps por parte de las redes demora o se rechaza | Alto | Empezar con una sola red; evaluar proveedor intermedio |
| Pocos datos de métricas por negocio | Medio | Reglas generales + reportes descriptivos hasta tener volumen |
| Calidad baja de fotos de los locales | Alto | Validación previa y guía al usuario al subir |
| Contenido incorrecto o riesgoso publicado | Alto | Aprobación humana + validaciones de copy |
| Costos de APIs y render se disparan | Medio | Caché, topes, monitoreo por negocio |
| Competir con herramientas establecidas en programación multi-red | Medio | No competir ahí; diferenciarse por el análisis de competencia |
| Nadie paga | Alto | Validar antes de construir etapas 2–4 |

---

## 12. Próximos pasos inmediatos

1. **Definir el catálogo inicial de plantillas** (3 para empezar): producto destacado, oferta/promoción, horario/apertura.
2. **Diseñar y fijar el esquema JSON de escena** con su validador.
3. **Prototipar el flujo foto → post** en el pipeline existente (sin publicar todavía).
4. **Agregar casos a `eval/`** para medir calidad del copy y de la elección de plantilla.
5. **Conseguir los primeros 5 locales** y agendar la demo.
6. **Revisar la documentación oficial de Instagram** para saber qué requisitos implica publicar, y planificar la etapa 2 con esa información.

---

## 13. Fuera de alcance (por ahora)

- Publicación en todas las redes a la vez.
- Publicación automática sin aprobación.
- Animación generativa fotográfica con modelos de video de terceros.
- Comparación de precios y alertas de movimientos de la competencia (evaluar en etapa 4).
- Planes pagos y facturación (después de validar interés).

---

## Glosario

- **FODA:** análisis de Fortalezas, Oportunidades, Debilidades y Amenazas.
- **Brand kit:** colores, tono, logo y tipografía del negocio.
- **Escena (JSON):** descripción estructurada de un video que el backend valida y renderiza con una plantilla.
- **Remotion:** herramienta para crear videos con código (React).
