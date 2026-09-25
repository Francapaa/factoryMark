"""Estado compartido del pipeline multi-agente (contrato entre nodos)."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    business_type: str = Field(examples=["café de especialidad"])
    zone: str = Field(examples=["Palermo Soho, Buenos Aires"])
    language: str = "es"


class Competitor(BaseModel):
    place_id: str
    name: str
    rating: float | None = None
    user_ratings_total: int = 0
    address: str = ""
    cached: bool = False  # True si vino de cache (ahorro de cuota)


class ReviewCluster(BaseModel):
    topic: str
    count: int
    avg_sentiment: float  # -1 .. 1
    example_texts: list[str] = []


class Opportunity(BaseModel):
    title: str
    evidence: str
    confidence: Literal["alta", "media", "baja"] = "media"


class DraftPost(BaseModel):
    copy_text: str
    hashtags: list[str] = []
    status: Literal["draft", "approved", "rejected"] = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalyzeResponse(BaseModel):
    competitors: list[Competitor] = []
    clusters: list[ReviewCluster] = []
    opportunities: list[Opportunity] = []
    draft_post: DraftPost | None = None
    meta: dict = {}
