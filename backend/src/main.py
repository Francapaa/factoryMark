"""FastAPI entrypoint - setup mínimo, sin llamadas pagas por defecto."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from publisher import build_draft, set_status
from state import AnalyzeRequest, AnalyzeResponse, DraftPost

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "places_configured": bool(settings.google_places_api_key),
        "limits": {
            "max_competitors": settings.max_competitors,
            "max_reviews_per_place": settings.max_reviews_per_place,
        },
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    # Stub intencional: no llama a Google Places hasta Fase Researcher.
    # Así no se gasta cuota durante el setup.
    return AnalyzeResponse(
        competitors=[],
        clusters=[],
        opportunities=[],
        draft_post=DraftPost(
            copy_text=f"Borrador para {req.business_type} en {req.zone} (pipeline aún no implementado)."
        ),
        meta={"stub": True, "message": "Researcher/Analyst pendientes de implementación"},
    )


class ApproveRequest(BaseModel):
    approved: bool
    opportunity_title: str = "horario de tarde sin competencia"
    brand_name: str = "Café Ejemplo"


@app.post("/api/approve", response_model=DraftPost)
def approve(req: ApproveRequest) -> DraftPost:
    # Mock sin persistencia: demuestra el human-in-the-loop.
    draft = build_draft(req.opportunity_title, {"name": req.brand_name, "tone": "cercano"})
    return set_status(draft, req.approved)


def run() -> None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run()
