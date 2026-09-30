"""Tests del contrato de escena. Cero red, cero render."""

import pytest
from pydantic import ValidationError

from video.scene import TEMPLATES, default_scene, validate_scene

PHOTOS = {"ph_001", "ph_004"}
AUDIOS = {"au_001"}

GOLDEN = {  # ejemplo project2.md §5.3
    "template": "producto_destacado_v1",
    "duration_seconds": 12,
    "aspect_ratio": "9:16",
    "scenes": [
        {"photo_id": "ph_001", "motion": "zoom_in_suave", "text": "Café de especialidad", "text_position": "bottom"},
        {"photo_id": "ph_004", "motion": "pan_izquierda", "text": "Abierto hasta las 21 h", "text_position": "center"},
    ],
    "cta": "Pasá esta tarde",
    "caption": "Mientras otros cierran temprano, nosotros seguimos acá.",
    "hashtags": ["#cafedebarrio", "#sanjusto"],
}


def test_catalogo_tres_plantillas():
    assert set(TEMPLATES) == {"producto_destacado_v1", "oferta_promocion_v1", "horario_apertura_v1"}


def test_ejemplo_dorado_valido():
    spec = validate_scene(GOLDEN, PHOTOS, AUDIOS)
    assert spec.template == "producto_destacado_v1"
    assert len(spec.scenes) == 2 and spec.cta == "Pasá esta tarde"


def test_template_desconocido_rechazado():
    with pytest.raises(ValidationError, match="template desconocido"):
        validate_scene({**GOLDEN, "template": "hollywood_v9"}, PHOTOS)


def test_motion_fuera_de_vocabulario():
    bad = {**GOLDEN, "scenes": [{**GOLDEN["scenes"][0], "motion": "giro mortal"}]}
    with pytest.raises(ValidationError):
        validate_scene(bad, PHOTOS)


def test_foto_ajena_rechazada():
    bad = {**GOLDEN, "scenes": [{**GOLDEN["scenes"][0], "photo_id": "competidor_01"}]}
    with pytest.raises(ValueError, match="no pertenece al negocio"):
        validate_scene(bad, PHOTOS)


def test_audio_ajeno_rechazado():
    bad = {**GOLDEN, "audio": {"audio_id": "spotify_xxx"}}
    with pytest.raises(ValueError, match="audio_id"):
        validate_scene(bad, PHOTOS, AUDIOS)


def test_audio_propio_y_silencio_validos():
    assert validate_scene({**GOLDEN, "audio": {"audio_id": "au_001"}}, PHOTOS, AUDIOS).audio is not None
    assert validate_scene(GOLDEN, PHOTOS).audio is None  # silencioso: válido


def test_url_html_y_js_rechazados():
    for field, value in [
        ("caption", "mirá http://evil.com"),
        ("cta", "click <b>acá</b>"),
        ("caption", "javascript:alert(1)"),
    ]:
        with pytest.raises(ValidationError, match="no se permiten"):
            validate_scene({**GOLDEN, field: value}, PHOTOS)


def test_hashtag_sin_numeral_rechazado():
    with pytest.raises(ValidationError, match="hashtag inválido"):
        validate_scene({**GOLDEN, "hashtags": ["promo"]}, PHOTOS)


def test_texto_largo_y_duracion_rechazados():
    with pytest.raises(ValidationError):
        validate_scene({**GOLDEN, "cta": "x" * 41}, PHOTOS)
    with pytest.raises(ValidationError):
        validate_scene({**GOLDEN, "duration_seconds": 61}, PHOTOS)
    with pytest.raises(ValidationError):
        validate_scene({**GOLDEN, "scenes": []}, PHOTOS)


def test_fallback_siempre_valido():
    spec = default_scene()
    assert validate_scene(spec.model_dump(), {"default"}).template == "producto_destacado_v1"
