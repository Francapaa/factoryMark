"""Contrato de escena de video: plantillas + JSON validado (sin código libre).

El LLM / pipeline solo produce datos; el render usa plantillas fijas.
Ver openspec/changes/video-module/specs/scene-schema/spec.md
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Motion = Literal["zoom_in_suave", "zoom_out_suave", "pan_izquierda", "pan_derecha", "estatico"]
TextPosition = Literal["top", "center", "bottom"]
MusicMood = Literal["calido_acustico", "energia_alta", "minimalista", "sin_musica"]

MAX_SCENES = 8
MAX_TEXT = 80
MAX_CTA = 40
MAX_CAPTION = 220
MAX_HASHTAGS = 5
MIN_DURATION_S = 5
MAX_DURATION_S = 60

_FORBIDDEN = re.compile(r"https?://|[<>]|javascript:", re.IGNORECASE)


def _clean(v: str, field: str) -> str:
    if _FORBIDDEN.search(v):
        raise ValueError(f"{field}: no se permiten URLs, HTML ni código")
    return v


class Template(BaseModel, frozen=True):
    name: str
    default_duration_s: int
    allowed_positions: tuple[TextPosition, ...]


TEMPLATES: dict[str, Template] = {
    "producto_destacado_v1": Template(
        name="producto_destacado_v1",
        default_duration_s=12,
        allowed_positions=("bottom", "center"),
    ),
    "oferta_promocion_v1": Template(
        name="oferta_promocion_v1",
        default_duration_s=10,
        allowed_positions=("center", "top"),
    ),
    "horario_apertura_v1": Template(
        name="horario_apertura_v1",
        default_duration_s=8,
        allowed_positions=("center", "bottom"),
    ),
}


class Scene(BaseModel):
    photo_id: str = Field(min_length=1)
    motion: Motion = "estatico"
    text: str = Field(max_length=MAX_TEXT, default="")
    text_position: TextPosition = "bottom"

    @field_validator("text")
    @classmethod
    def _text_safe(cls, v: str) -> str:
        return _clean(v, "text")


class AudioTrack(BaseModel):
    """Audio subido por el dueño. Ausente = render silencioso."""

    audio_id: str = Field(min_length=1)
    music_mood: MusicMood = "sin_musica"


class SceneSpec(BaseModel):
    template: str
    duration_seconds: int = Field(ge=MIN_DURATION_S, le=MAX_DURATION_S)
    aspect_ratio: Literal["9:16"] = "9:16"
    audio: AudioTrack | None = None
    scenes: list[Scene] = Field(min_length=1, max_length=MAX_SCENES)
    cta: str = Field(max_length=MAX_CTA, default="")
    caption: str = Field(max_length=MAX_CAPTION, default="")
    hashtags: list[str] = Field(default_factory=list, max_length=MAX_HASHTAGS)

    @field_validator("template")
    @classmethod
    def _template_exists(cls, v: str) -> str:
        if v not in TEMPLATES:
            raise ValueError(f"template desconocido; válidos: {sorted(TEMPLATES)}")
        return v

    @field_validator("cta", "caption")
    @classmethod
    def _copy_safe(cls, v: str, info) -> str:
        return _clean(v, info.field_name)

    @field_validator("hashtags")
    @classmethod
    def _hashtags_valid(cls, v: list[str]) -> list[str]:
        for h in v:
            if not h.startswith("#") or len(h) < 2:
                raise ValueError(f"hashtag inválido: {h!r} (debe empezar con #)")
            _clean(h, "hashtags")
        return v

    @field_validator("scenes")
    @classmethod
    def _positions_allowed(cls, v: list[Scene], info) -> list[Scene]:
        template = (info.data or {}).get("template")
        if template in TEMPLATES:
            allowed = TEMPLATES[template].allowed_positions
            for s in v:
                if s.text and s.text_position not in allowed:
                    raise ValueError(
                        f"text_position {s.text_position!r} no permitido en {template}"
                    )
        return v


def validate_scene(data: dict, photo_ids: set[str], audio_ids: set[str] | None = None) -> SceneSpec:
    """Valida contrato + pertenencia de assets al negocio. Lanza ValidationError/ValueError."""
    audio_ids = audio_ids or set()
    spec = SceneSpec(**data)
    unknown_photos = {s.photo_id for s in spec.scenes} - photo_ids
    if unknown_photos:
        raise ValueError(f"photo_id no pertenece al negocio: {sorted(unknown_photos)}")
    if spec.audio and spec.audio.audio_id not in audio_ids:
        raise ValueError(f"audio_id no pertenece al negocio: {spec.audio.audio_id!r}")
    return spec


def default_scene() -> SceneSpec:
    """Fallback: plantilla por defecto, silenciosa, una escena estática."""
    return SceneSpec(
        template="producto_destacado_v1",
        duration_seconds=TEMPLATES["producto_destacado_v1"].default_duration_s,
        scenes=[Scene(photo_id="default", motion="estatico", text="")],
    )
