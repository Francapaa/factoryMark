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

1. **Investiga tu comercio y tu zona.** Le decís el nombre de tu negocio, qué tipo es, dónde está y cómo vendés (local, online o mixto). Si es local, busca competidores cercanos en Google Maps; si es online, rastrea quién vende lo mismo en la web.
2. **Lee las opiniones por vos.** Analiza reseñas reales de Google (y menciones web en modo online) y agrupa de qué habla la gente: la espera, los precios, la atención, la calidad.
3. **Encuentra tu oportunidad.** Cruza toda esa información y detecta huecos concretos. Por ejemplo: "dos competidores tienen muchas quejas por la demora" o "nadie promociona el horario de la tarde".
4. **Te escribe la publicación.** Con esa oportunidad, redacta un texto para redes con el tono y los colores de tu marca, listo para revisar.
5. **Vos tenés la última palabra.** Nada se publica solo: la publicación queda en borrador y vos la aprobás o la rechazás con un clic.

## Estado actual del proyecto

Estamos en etapa de **demo técnica**. Hoy el sistema ya hace esto:

- ✅ Recibe tu comercio (nombre obligatorio + canal: local/online/mixto) desde la página web y corre el pipeline real.
- ✅ Busca competidores por cercanía en Google Maps (con reseñas, horarios y fotos reales si configurás la key) o en la web vía Tavily para tiendas online.
- ✅ Detecta oportunidades con reglas claras y genera un borrador de publicación.
- ✅ El flujo completo funciona encadenado: investigar → analizar → detectar → redactar → dejar listo para aprobar.
- ⏳ Sin API keys usa datos de ejemplo (marcados como tales); la publicación automática en Instagram queda para Fase 3. Las métricas de redes (frecuencia, engagement) son Fase 2 vía Apify, pago.

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

Después abrí http://localhost:3000 en tu navegador: escribí el nombre de tu comercio, tipo de negocio, zona y canal de venta, y vas a ver competidores, oportunidades detectadas y un borrador de publicación con botones para aprobar o rechazar.

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
