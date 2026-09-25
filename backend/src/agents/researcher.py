"""Researcher: competidores + reviews (STUB local, cero llamadas externas).

Wave futura: reemplazar el cuerpo por `tools.places.search_competitors`
+ `fetch_reviews` manteniendo la firma y el formato de salida.
"""

from __future__ import annotations

_FIXTURE_REVIEWS: dict[str, list[str]] = {
    "p1": [
        "El café es riquísimo y la atención excelente, vuelvo siempre",
        "Lugar hermoso, merienda increíble y personal muy amable",
        "Todo delicioso, el mejor café de especialidad del barrio",
        "Excelente atención, rápido y muy recomendable",
        "Me encanta este lugar, el flat white es perfecto",
        "Buenísimo todo, lindo ambiente y precios razonables",
        "Espectacular la pastelería, fresca y deliciosa",
        "Atención genial, se nota que aman lo que hacen",
    ],
    "p2": [
        "Pésima atención, esperé 40 minutos y el café llegó frío",
        "Muy caro para lo que es, porciones chicas y mala onda",
        "Café quemado y amargo, una decepción total",
        "Lentísimo todo, nunca más vuelvo a este lugar",
        "La comida llegó fría y cruda, horrible experiencia",
        "Precios carísimos y calidad mala, no lo recomiendo",
    ],
}


def researcher_node(state: dict) -> dict:
    competitors = [
        {
            "place_id": "p1",
            "name": "Café de Especialidad A",
            "rating": 4.6,
            "user_ratings_total": 842,
            "address": "Palermo Soho",
            "cached": True,
        },
        {
            "place_id": "p2",
            "name": "Café B",
            "rating": 3.4,
            "user_ratings_total": 210,
            "address": "Palermo Hollywood",
            "cached": True,
        },
    ]
    return {
        "competitors": competitors,
        "reviews_by_place": _FIXTURE_REVIEWS,
        "trace": ["researcher"],
    }
