"""Flujo analizar → aprobar (requiere auth)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import CurrentUser, get_current_user
from graph import run_analysis
from publisher import build_draft, set_status
from state import AnalyzeRequest, AnalyzeResponse, DraftPost
from tools.places import AnchorNotFoundError

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    req: AnalyzeRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AnalyzeResponse:
    try:
        saved = db.get_my_business(user.id)
    except RuntimeError as exc:  # DATABASE_URL ausente: fail fast, mensaje claro
        raise HTTPException(status_code=503, detail=str(exc))
    if saved is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "onboarding_incompleto",
                "message": "Completá el onboarding para registrar tu local antes de analizar",
            },
        )
    try:
        # El análisis corre sobre el negocio confirmado y guardado, nunca sobre
        # input sin confirmar (el dueño no renombra: el anchor es canónico).
        result = run_analysis(
            saved["name"], saved["business_type"], saved["zone"], saved["sales_channel"]
        )
    except AnchorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:  # config faltante (keys) u otro error explícito
        raise HTTPException(status_code=400, detail=str(exc))
    meta = result.get("meta") or {}
    meta["user_id"] = user.id
    return AnalyzeResponse(
        competitors=result.get("competitors", []),
        clusters=result.get("clusters", []),
        opportunities=result.get("opportunities", []),
        draft_post=result.get("draft_post"),
        meta=meta,
    )


class ApproveRequest(BaseModel):
    approved: bool
    opportunity_title: str = "horario de tarde sin competencia"
    brand_name: str = "Café Ejemplo"


@router.post("/approve", response_model=DraftPost)
def approve(
    req: ApproveRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> DraftPost:
    # Mock sin persistencia: demuestra el human-in-the-loop.
    _ = user  # el user_id queda disponible para auditar la aprobación en Fase 3
    draft = build_draft(req.opportunity_title, {"name": req.brand_name, "tone": "cercano"})
    return set_status(draft, req.approved)
