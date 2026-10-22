"""Flujo analizar → aprobar (requiere auth)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import CurrentUser, get_current_user
from graph import run_analysis
from publisher import build_draft, set_status
from state import AnalysisInfo, AnalyzeRequest, AnalyzeResponse, DraftPost
from tools.places import AnchorNotFoundError

logger = logging.getLogger("factorymark.analysis")

router = APIRouter(prefix="/api", tags=["analysis"])


def _saved_business_or_409(user: CurrentUser) -> dict:
    try:
        saved = db.get_my_business(user.id)
    except RuntimeError as exc:  # DATABASE_URL ausente: fail fast, mensaje claro
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # DB caída: no expongas el error interno
        logger.exception("No se pudo leer el negocio guardado de %s", user.id)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "db_no_disponible",
                "message": "No pudimos leer tu negocio guardado. Reintentá.",
            },
        ) from exc
    if saved is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "onboarding_incompleto",
                "message": "Completá el onboarding para registrar tu local antes de analizar",
            },
        )
    return saved


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    req: AnalyzeRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AnalyzeResponse:
    saved = _saved_business_or_409(user)
    try:
        # El análisis corre sobre el negocio confirmado y guardado, nunca sobre
        # input sin confirmar (el dueño no renombra: el anchor es canónico).
        result = run_analysis(
            saved["name"],
            saved["business_type"],
            saved["zone"],
            saved["sales_channel"],
            refresh_places=req.refresh_places,
        )
    except AnchorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:  # config faltante (keys) u otro error explícito
        raise HTTPException(status_code=400, detail=str(exc))

    meta = result.get("meta") or {}
    meta["user_id"] = user.id

    try:
        saved_run = db.save_analysis_run(
            saved["id"],
            competitors=result.get("competitors", []),
            opportunities=result.get("opportunities", []),
            clusters=result.get("clusters", []),
            draft_post=result.get("draft_post"),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("No se pudo guardar el análisis del negocio %s", saved["id"])
        raise HTTPException(
            status_code=503,
            detail={
                "code": "analisis_no_guardado",
                "message": "No pudimos guardar el análisis. Reintentá.",
            },
        ) from exc

    new_competitors = set(saved_run["new_competitor_ids"])
    new_opportunities = set(saved_run["new_opportunity_keys"])
    competitors = [
        {**comp, "is_new": comp["place_id"] in new_competitors}
        for comp in result.get("competitors", [])
    ]
    opportunities = [
        {**opp, "is_new": opp["key"] in new_opportunities}
        for opp in result.get("opportunities", [])
    ]
    return AnalyzeResponse(
        competitors=competitors,
        clusters=result.get("clusters", []),
        opportunities=opportunities,
        draft_post=result.get("draft_post"),
        meta=meta,
        analysis=AnalysisInfo(**saved_run["analysis"]),
    )


@router.get("/analysis/latest", response_model=AnalyzeResponse)
def latest_analysis(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AnalyzeResponse:
    saved = _saved_business_or_409(user)
    try:
        latest = db.get_latest_analysis(saved["id"])
    except Exception as exc:
        logger.exception("No se pudo leer el último análisis del negocio %s", saved["id"])
        raise HTTPException(
            status_code=503,
            detail={
                "code": "db_no_disponible",
                "message": "No pudimos leer tu análisis guardado. Reintentá.",
            },
        ) from exc
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "sin_analisis",
                "message": "Todavía no hay un análisis guardado para este negocio",
            },
        )
    return AnalyzeResponse(**latest)


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
