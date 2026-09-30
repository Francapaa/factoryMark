# FactoryMark Backend

Agente de Inteligencia Competitiva — FastAPI.

## Setup (uv)

```powershell
cd backend
uv sync
uv run pytest
uv run dev.py   # dev server con reload en 127.0.0.1:8000 (ver dev.py)
```

- `GET /health` → estado + keys configuradas + límites de cuota.
- `POST /api/analyze` → pipeline real. Requiere `business_name` + `business_type`
  + `zone` + `sales_channel` (`local|online|mixto`). Sin `business_name` → 422;
  si el comercio no se encuentra en Maps → 404 (nunca fixtures silenciosas).

## Cuidar cuota ($20)

- Límites en `src/config.py`: `max_competitors=10`, `max_reviews_per_place=20`,
  `search_radius_m=1000`, `tavily_max_queries=3`, `tavily_max_results=5`.
- Cache de 7 días en `backend/data/cache/` (Search, Details, anchor y Tavily
  por separado): segundo análisis igual = cero llamadas pagas.
- Tavily (~$0.01/búsqueda) solo es obligatorio en canal `online`/`mixto`.
- `.env` nunca se commitea. Usar `.env.example` como base.

## Límites conocidos

- Places Details devuelve ~5 reviews por lugar: los clusters agregan todos los
  competidores (~50 textos), suficiente para TF-IDF/KMeans.
- Métricas de redes (frecuencia, engagement) NO están incluidas: son Fase 2
  vía Apify (pago). Tavily solo aporta links a perfiles, nunca métricas.

## Evaluación

Desde `backend/`: `uv run python ../eval/run.py` (casos en `eval/golden_set.json`,
rúbrica en `eval/rubric.md`). Sin keys corre sobre fixtures (baseline).
