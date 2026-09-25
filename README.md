# FactoryMark

**Tu espía legal de la competencia, que además te escribe el marketing.**

FactoryMark es un asistente con inteligencia artificial pensado para negocios de barrio: cafés, restaurantes, barberías, panaderías y comercios chicos en general. Hace automáticamente lo que ningún dueño tiene tiempo de hacer: mirar qué está haciendo la competencia, detectar en qué le podés ganar y prepararte una publicación lista para atraer esos clientes.

## El problema que resuelve

Si tenés un local, probablemente te pasa esto:

- No tenés tiempo de fijarte qué hacen los negocios parecidos al tuyo en la zona.
- Las opiniones de Google (tuyas y las de ellos) esconden información valiosísima, pero nadie las lee todas.
- Aunque detectaras una oportunidad ("nadie abre a la tarde"), convertirla en una buena publicación lleva tiempo y oficio.

FactoryMark automatiza ese ciclo completo: **mira → detecta → te prepara la jugada**.

## Qué hace, paso a paso

1. **Investiga tu zona.** Le decís qué tipo de negocio tenés y dónde está (por ejemplo: "café de especialidad en Palermo Soho"). Busca tus competidores cercanos y sus opiniones públicas de Google.
2. **Lee las opiniones por vos.** Analiza cientos de reseñas y agrupa de qué habla la gente: la espera, los precios, la atención, la calidad. Detecta si un lugar viene mejorando o empeorando.
3. **Encuentra tu oportunidad.** Cruza toda esa información y detecta huecos concretos. Por ejemplo: "dos competidores tienen muchas quejas por la demora" o "nadie promociona el horario de la tarde".
4. **Te escribe la publicación.** Con esa oportunidad, redacta un texto para redes con el tono y los colores de tu marca, listo para revisar.
5. **Vos tenés la última palabra.** Nada se publica solo: la publicación queda en borrador y vos la aprobás o la rechazás con un clic.

## Estado actual del proyecto

Estamos en etapa de **demo técnica**. Hoy el sistema ya hace esto:

- ✅ Recibe tu tipo de negocio y tu zona desde una página web simple.
- ✅ Busca competidores con datos de ejemplo y analiza reseñas de verdad con su propio sistema (sin inventar nada).
- ✅ Detecta oportunidades con reglas claras y genera un borrador de publicación.
- ✅ El flujo completo funciona encadenado: investigar → analizar → detectar → redactar → dejar listo para aprobar.
- ⏳ Falta conectar los datos reales de Google y la publicación automática en Instagram (a propósito, para no gastar dinero en pruebas).

## Cómo probarlo

Necesitás tener instalado `uv` (para el sistema) y `pnpm` (para la página web).

**1. Poner en marcha el sistema:**

```powershell
cd backend
uv sync
uv run uvicorn main:app --app-dir src --reload
```

**2. Abrir la página web (en otra terminal):**

```powershell
cd frontend
pnpm install
pnpm dev
```

Después abrí http://localhost:3000 en tu navegador: escribí un tipo de negocio y una zona, y vas a ver competidores, oportunidades detectadas y un borrador de publicación con botones para aprobar o rechazar.

## Cómo está organizado

```
factoryMark/
  project.md    # El diseño completo del proyecto (versión técnica)
  eval/         # Casos de prueba para medir si el sistema acierta
  brand_kits/   # Los datos de tu marca: nombre, colores, tono
  backend/      # El cerebro: investiga, analiza y redacta
  frontend/     # La página web donde ves los resultados
```

## Cuidado con los costos

Consultar datos de Google cuesta dinero (empezamos con 20 dólares). Por eso el sistema está diseñado para gastar lo mínimo: guarda todo en caché por 7 días, pone límites a la cantidad de consultas y las pruebas usan datos de ejemplo que no cuestan nada.

## A dónde va esto

- **Fase 1 (actual):** demo técnica funcionando de punta a punta.
- **Fase 2:** mostrarla a 5–10 dueños de locales reales y ver si les sirve de verdad.
- **Fase 3 (solo si hay interés):** conexión real con Google e Instagram, comparación de precios, alertas automáticas cuando un competidor se mueve y planes pagos.
