"""Tests del Estratega ampliado: asignación única de citas y tope de ejemplos."""

from agents.strategist import strategist_node


def _evidences(opportunities: list[dict]) -> str:
    return "\n".join(o["evidence"] for o in opportunities)


def test_misma_review_en_rating_y_categoria_sale_una_vez():
    t1 = "Una vergüenza, todo carísimo y precios por las nubes"
    t2 = "Muy caro para lo que dan, no vuelvo"
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": [t1, t2]},
            "review_ratings": {"p1": [1, 2]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert opps[0]["title"] == "Dolor rival: precios altos (2 menciones)"
    joined = _evidences(opps)
    assert joined.count(t1[:40]) == 1
    assert joined.count(t2[:40]) == 1


def test_rating_solo_para_sin_categoria():
    t1 = "No vuelvo más, todo mal"
    t2 = "Jamás regreso, mal todo"
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": [t1, t2]},
            "review_ratings": {"p1": [1, 1]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert opps[0]["title"] == "Dolor rival: 2 reviews de 1-2 estrellas"


def test_tope_tres_ejemplos_con_mas_menciones():
    texts = [f"Esperé {i}0 minutos, lentísimo todo, un desastre" for i in range(5)]
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": texts},
            "review_ratings": {"p1": [2, 2, 2, 2, 2]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert "(5 menciones)" in opps[0]["title"]
    assert opps[0]["confidence"] == "alta"
    examples_part = opps[0]["evidence"].split("Ej:")[1]
    assert examples_part.count(";") == 2  # 3 citas como máximo


def test_evidencia_cita_review_completa():
    larga = (
        "Todo muy lindo al principio pero al final la cuenta fue un robo, "
        "carísimo para lo que comimos, una vergüenza total y no pienso volver "
        "nunca más a este lugar, la cuenta un desastre"
    )
    assert len(larga) > 160
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": [larga, "Carísimo todo, precios por las nubes"]},
            "review_ratings": {"p1": [2, 1]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert larga in opps[0]["evidence"]


def test_sin_falsos_positivos_de_substring():
    # "buscarlo"/"carta"/"carne" no son precio; "a la tarde" no es demora.
    # (Con sentimiento negativo para que lleguen al regex y no se filtren antes.)
    texts = [
        "Pésima la atención a la tarde, mandaron a buscarlo a la carta",
        "Horrible la carne y la carta, nunca más a la tarde",
    ]
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": texts},
            "review_ratings": {"p1": [5, 5]},
        }
    )
    titles = [o["title"] for o in out["opportunities"]]
    assert not any("precios altos" in t or "esperas" in t for t in titles)


def test_dolor_general_una_card_por_review():
    # Dos dolores en buckets distintos (1+1): ninguno llega a 2,
    # cada reseña es su propia card con negocio. Nada concatenado.
    t1 = "Esperé 40 minutos, lentísimo todo"
    t2 = "Carísimo todo, precios por las nubes"
    out = strategist_node(
        {
            "clusters": [],
            "competitors": [{"place_id": "p1", "name": "Café B"}],
            "reviews_by_place": {"p1": [t1, t2]},
            "review_ratings": {"p1": [1, 1]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 2
    assert all("Café B" in o["title"] for o in opps)
    joined = _evidences(opps)
    assert joined.count(t1[:40]) == 1
    assert joined.count(t2[:40]) == 1
    assert ";" not in joined  # ninguna evidencia junta dos reviews


def test_bucket_atribuye_negocio_por_cita():
    t1 = "Carísimo todo, precios por las nubes"
    t2 = "Muy caro para lo que dan"
    out = strategist_node(
        {
            "clusters": [],
            "competitors": [
                {"place_id": "p1", "name": "Café B"},
                {"place_id": "p2", "name": "Bar C"},
            ],
            "reviews_by_place": {"p1": [t1], "p2": [t2]},
            "review_ratings": {"p1": [1], "p2": [2]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert "— Café B" in opps[0]["evidence"]
    assert "— Bar C" in opps[0]["evidence"]


def test_elogio_largo_con_nunca_no_es_dolor():
    # Caso AGUSTINA: 5★, un "nunca" perdido en un elogio largo da -0.06,
    # que con el umbral < -0.2 queda afuera.
    praise = (
        "Quiero contar que pedí delivery y me atendió Agustina con paciencia "
        "y amabilidad como nunca me pasó, me ayudó en todos los pasos y me mandó "
        "de cortesía unos bombones, solo decirte gracias"
    )
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {"p1": [praise]},
            "review_ratings": {"p1": [5]},
        }
    )
    opps = out["opportunities"]
    assert len(opps) == 1
    assert opps[0]["confidence"] == "baja"


def test_patrones_nuevos_atiende_y_pedido():
    out = strategist_node(
        {
            "clusters": [],
            "reviews_by_place": {
                "p1": [
                    "Nadie atiende el teléfono, pésimo",
                    "Nadie atiende nunca, malísimo",
                    "El pedido nunca llegó a casa",
                    "Mi pedido nunca llegó, espantoso",
                ]
            },
            "review_ratings": {"p1": [2, 1, 2, 1]},
        }
    )
    titles = [o["title"] for o in out["opportunities"]]
    assert any("mal servicio" in t for t in titles)
    assert any("esperas" in t for t in titles)


def test_ejemplo_de_cluster_no_se_repite_en_categoria():
    x = "Esperé una hora, lentísimo y carísimo además"
    out = strategist_node(
        {
            "clusters": [
                {"topic": "espera", "count": 3, "avg_sentiment": -0.6, "example_texts": [x]}
            ],
            "reviews_by_place": {"p1": [x, "Esperé 40 minutos otra vez"]},
            "review_ratings": {"p1": [1, 2]},
        }
    )
    joined = _evidences(out["opportunities"])
    assert joined.count(x[:40]) == 1


def test_key_categoria_estable_cuando_cambia_el_conteo():
    def run(n: int) -> list[dict]:
        return strategist_node(
            {
                "clusters": [],
                "reviews_by_place": {"p1": ["Carísimo todo"] * n},
                "review_ratings": {"p1": [1] * n},
            }
        )["opportunities"]

    first = run(2)
    later = run(5)
    assert first[0]["key"] == later[0]["key"] == "category:precios-altos"
    assert first[0]["title"] != later[0]["title"]


def test_keys_de_cluster_y_fallback():
    clustered = strategist_node(
        {
            "clusters": [
                {"topic": "Esperas y demoras", "count": 3, "avg_sentiment": -0.6}
            ]
        }
    )["opportunities"]
    assert clustered[0]["key"] == "cluster:esperas-y-demoras"

    fallback = strategist_node(
        {"clusters": [{"topic": "todo bien", "count": 10, "avg_sentiment": 0.8}]}
    )["opportunities"]
    assert fallback[0]["key"] == "none"


def test_cluster_general_no_tapa_las_categorias():
    t1 = "Carísimo todo, precios por las nubes"
    t2 = "Muy caro para lo que dan"
    out = strategist_node(
        {
            "clusters": [
                {
                    "topic": "general",
                    "count": 2,
                    "avg_sentiment": -0.8,
                    "example_texts": [t1, t2],
                }
            ],
            "reviews_by_place": {"p1": [t1, t2]},
            "review_ratings": {"p1": [1, 1]},
        }
    )
    assert [o["key"] for o in out["opportunities"]] == ["category:precios-altos"]


def test_key_de_review_individual_es_estable():
    state = {
        "clusters": [],
        "reviews_by_place": {"p1": ["Jamás regreso", "Terrible experiencia"]},
        "review_ratings": {"p1": [3, 3]},
    }
    first = strategist_node(state)["opportunities"]
    later = strategist_node(state)["opportunities"]
    assert [o["key"] for o in first] == [o["key"] for o in later]
    assert all(o["key"].startswith("review:p1:") for o in first)
