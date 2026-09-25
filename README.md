# FactoryMark — Agente de Inteligencia Competitiva

Ver `project.md` para el diseño completo.

Pipeline: `Researcher → Analyst → Strategist → Creator → Publisher` con human-in-the-loop.

## Estructura

```
factoryMark/
  project.md
  backend/    # Python + FastAPI con uv
  frontend/   # Next.js + Tailwind con pnpm
```

## Requisitos

- `uv`, Python 3.12+
- Node 24+, `pnpm`

## Backend

```powershell
cd backend
uv sync
uv run pytest
uv run uvicorn main:app --app-dir src --reload
```

- `GET /health`
- `POST /api/analyze` (stub, no gasta cuota)

Config: copiar `backend/.env.example` a `backend/.env` y cargar `GOOGLE_PLACES_API_KEY`.

## Frontend

```powershell
cd frontend
cp .env.local.example .env.local
pnpm install
pnpm dev
```

Abre http://localhost:3000 — muestra estado del backend.

## Ahorro de cuota ($20)

- `max_competitors=10`, `max_reviews_per_place=20` en `backend/src/config.py`.
- Cache de Places de 7 días (a implementar en Researcher).
- El stub actual no hace llamadas pagas.

## Siguiente paso

Fase Researcher: cliente Google Places (New) con dedup + cache en disco + tests con fixtures.
