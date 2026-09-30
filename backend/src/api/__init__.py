"""Routers HTTP agrupados por dominio (no por endpoint)."""

from fastapi import APIRouter

from api.analysis import router as analysis_router
from api.businesses import router as businesses_router
from api.public import router as public_router

api_router = APIRouter()
api_router.include_router(public_router)
api_router.include_router(businesses_router)
api_router.include_router(analysis_router)
