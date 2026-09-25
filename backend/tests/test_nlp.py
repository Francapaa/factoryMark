"""Tests Analyst: clustering separa quejas de elogios, sentiment y scoring."""

from datetime import UTC, datetime, timedelta

from factorymark.nlp.cluster import cluster_reviews
from factorymark.nlp.embeddings import embed_texts
from factorymark.nlp.scoring import competitive_score
from factorymark.nlp.sentiment import score_sentiment, trend_by_month

PRAISE = [
    "El café es riquísimo y la atención excelente, vuelvo siempre",
    "Lugar hermoso, merienda increíble y personal muy amable",
    "Todo delicioso, el mejor café de especialidad del barrio",
    "Excelente atención, rápido y muy recomendable",
    "Me encanta este lugar, el flat white es perfecto",
    "Buenísimo todo, lindo ambiente y precios razonables",
    "Espectacular la pastelería, fresca y deliciosa",
    "Atención genial, se nota que aman lo que hacen",
    "El mejor lugar para trabajar, wifi rápido y café increíble",
    "Volveré seguro, experiencia perfecta de punta a punta",
    "Riquísimo el brunch, porciones generosas y ricas",
    "Hermoso local, impecable y con muy buena onda",
    "Café de especialidad de verdad, se nota la calidad",
    "Delicioso todo, la torta de chocolate es un 10",
    "Excelente relación precio calidad, lo recomiendo",
    "Personal amable y atento, te hacen sentir en casa",
]
COMPLAINTS = [
    "Pésima atención, esperé 40 minutos y el café llegó frío",
    "Muy caro para lo que es, porciones chicas y mala onda",
    "El lugar estaba sucio y las mesas sin limpiar",
    "Café quemado y amargo, una decepción total",
    "Lentísimo todo, nunca más vuelvo a este lugar",
    "La comida llegó fría y cruda, horrible experiencia",
    "Precios carísimos y calidad mala, no lo recomiendo",
    "Atención mala, el mozo fue maleducado con nosotros",
    "Ruidoso, incómodo y con poca variedad en la carta",
    "Reservé y no respetaron mi mesa, pésimo servicio",
    "El baño estaba sucio, un asco la higiene",
    "Me cobraron de más y se hicieron los distraídos",
    "Café aguado y frío, nada que ver con lo que prometen",
    "Nunca hay lugar, no organizan la fila y atienden mal",
]


def test_embed_texts_shape():
    vecs = embed_texts(["hola mundo", "café rico"])
    assert len(vecs) == 2 and len(vecs[0]) > 0
    assert embed_texts([]) == []


def test_cluster_separa_elogios_y_quejas():
    clusters = cluster_reviews(PRAISE + COMPLAINTS)
    assert 2 <= len(clusters) <= 5
    assert sum(c.count for c in clusters) == len(PRAISE + COMPLAINTS)
    sentiments = sorted(c.avg_sentiment for c in clusters)
    assert sentiments[0] < 0 < sentiments[-1]  # hay polo negativo y positivo


def test_cluster_pocos_textos_un_grupo():
    clusters = cluster_reviews(["rico todo", "muy bueno"])
    assert len(clusters) == 1 and clusters[0].count == 2


def test_sentiment_polaridad_y_negacion():
    assert score_sentiment("Excelente café, riquísimo y recomendable") > 0.2
    assert score_sentiment("Horrible, café frío y pésima atención") < -0.2
    assert score_sentiment("No es bueno, no lo recomiendo") < 0
    assert score_sentiment("") == 0.0


def test_trend_by_month():
    now = datetime.now(UTC)
    reviews = [
        ((now - timedelta(days=60)).isoformat(), "Horrible todo, pésimo"),
        ((now - timedelta(days=5)).isoformat(), "Excelente, riquísimo todo"),
    ]
    trend = trend_by_month(reviews)
    assert len(trend) == 2
    months = sorted(trend)
    assert trend[months[0]] < trend[months[-1]]  # mejoró con el tiempo


def test_scoring_orden_y_bordes():
    bueno = competitive_score(4.8, 1500, datetime.now(UTC).isoformat(), 5)
    malo = competitive_score(3.0, 20, "2020-01-01T00:00:00+00:00", 0)
    assert 0 <= malo < bueno <= 1
    assert competitive_score(None, 0, None, 0) == 0.0
    assert competitive_score(5.0, 100000, datetime.now(UTC).isoformat(), 100) <= 1.0
