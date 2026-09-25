# FactoryMark Backend

Agente de Inteligencia Competitiva — FastAPI.

## Setup (uv)

```powershell
cd backend
uv sync
uv run pytest
uv run uvicorn main:app --app-dir src --reload
```

- `GET /health` → estado + si hay Places key + límites de cuota.
- `POST /api/analyze` → stub (no gasta cuota). Researcher real en próxima fase.

## Cuidar cuota ($20)

- Límites en `src/config.py`: `max_competitors=10`, `max_reviews_per_place=20`.
- Cache de Places de 7 días (a implementar en Researcher).
- `.env` nunca se commitea. Usar `.env.example` como base.
