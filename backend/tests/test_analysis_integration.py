"""Integración real: Postgres de test + Places simulado solo en HTTP.

No se mockea la capa de datos ni el pipeline. Si una corrida no se guarda,
el endpoint debe fallar, nunca devolver un éxito sin respaldo.
"""

from __future__ import annotations

import psycopg
import pytest
from psycopg.rows import dict_row

import db

pytestmark = pytest.mark.integration

ANCHOR = {
    "id": "anchor-1",
    "displayName": {"text": "Café Test"},
    "formattedAddress": "Calle Test 123",
    "location": {"latitude": -34.58, "longitude": -58.43},
}
COMP_A = {
    "id": "p-a",
    "displayName": {"text": "Café A"},
    "rating": 4.2,
    "userRatingCount": 120,
    "formattedAddress": "Calle A 1",
    "location": {"latitude": -34.581, "longitude": -58.431},
}
COMP_B = {
    "id": "p-b",
    "displayName": {"text": "Café B"},
    "rating": 2.9,
    "userRatingCount": 80,
    "formattedAddress": "Calle B 2",
    "location": {"latitude": -34.582, "longitude": -58.432},
}


def _details(place_id: str, reviews: list[tuple[str, int]]) -> dict:
    return {
        "id": place_id,
        "websiteUri": f"https://{place_id}.example",
        "regularOpeningHours": {"weekdayDescriptions": ["lunes: 8–20"]},
        "photos": [{"name": f"places/{place_id}/photos/1"}],
        "reviews": [
            {
                "text": {"text": text},
                "authorAttribution": {"displayName": "Ana"},
                "rating": rating,
                "publishTime": "2026-09-01T12:00:00Z",
            }
            for text, rating in reviews
        ],
    }


DETAILS = {
    "p-a": _details(
        "p-a",
        [
            ("Esperé 40 minutos y el café llegó frío", 1),
            ("Lentísimo, nunca llegó el pedido", 1),
        ],
    ),
    "p-b": _details(
        "p-b",
        [
            ("Carísimo para lo que es", 1),
            ("Precios altos y porciones chicas", 1),
            ("Muy caro, no vuelvo", 1),
        ],
    ),
}


def _competitor(place_id: str, name: str) -> dict:
    return {
        "place_id": place_id,
        "name": name,
        "rating": 4.0,
        "user_ratings_total": 10,
        "address": "Calle 1",
        "cached": False,
        "source": "maps",
        "distance_m": 15.0,
    }


def _rows(url: str, sql: str, params: dict | None = None) -> list[dict]:
    with psycopg.connect(url, row_factory=dict_row) as conn:
        return conn.execute(sql, params or {}).fetchall()


def _count(url: str, table: str, business_id: str) -> int:
    rows = _rows(
        url,
        f"SELECT count(*) AS n FROM {table} WHERE business_id = %(id)s::uuid",
        {"id": business_id},
    )
    return int(rows[0]["n"])


def _analyze_body(refresh_places: bool = True) -> dict:
    return {
        "business_name": "Café Test",
        "business_type": "café de especialidad",
        "zone": "Palermo Soho",
        "sales_channel": "local",
        "refresh_places": refresh_places,
    }


def test_analizar_persiste_y_latest_devuelve_lo_guardado(
    client,
    configured_db,
    clean_tables,
    as_user,
    create_business,
    fake_places,
):
    business = create_business("owner-a")
    fake_places.configure(
        anchor=ANCHOR,
        competitors=[COMP_A, COMP_B],
        details={key: DETAILS[key] for key in ("p-a", "p-b")},
    )
    as_user("owner-a")

    response = client.post(
        "/api/analyze",
        json={
            "business_name": "Otro nombre",
            "business_type": "bar",
            "zone": "Belgrano",
            "sales_channel": "online",
            "refresh_places": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert fake_places.queries and fake_places.queries[0] == "Café Test, Palermo Soho"
    assert {c["place_id"] for c in body["competitors"]} == {"p-a", "p-b"}
    assert len(body["opportunities"]) >= 2
    assert body["analysis"]["new_competitors"] == 0
    assert body["analysis"]["new_opportunities"] == 0
    assert body["analysis"]["competitors_count"] == 2
    assert body["analysis"]["opportunities_count"] == len(body["opportunities"])
    assert all(c["is_new"] is False for c in body["competitors"])
    assert all(o["is_new"] is False for o in body["opportunities"])
    assert body["meta"]["stub"] is False

    runs = _rows(
        configured_db,
        """
        SELECT id, competitors_count, opportunities_count
          FROM app.analisis
         WHERE business_id = %(id)s::uuid
        """,
        {"id": business["id"]},
    )
    assert len(runs) == 1
    assert str(runs[0]["id"]) == body["analysis"]["id"]
    assert runs[0]["competitors_count"] == 2
    assert _count(configured_db, "app.competidores", business["id"]) == 2
    assert _count(configured_db, "app.oportunidades", business["id"]) == len(
        body["opportunities"]
    )

    latest = client.get("/api/analysis/latest")
    assert latest.status_code == 200, latest.text
    latest_body = latest.json()
    assert latest_body["analysis"]["id"] == body["analysis"]["id"]
    assert latest_body["analysis"]["analyzed_at"] == body["analysis"]["analyzed_at"]
    assert latest_body["analysis"]["new_competitors"] == 0
    assert latest_body["analysis"]["new_opportunities"] == 0
    assert {c["place_id"] for c in latest_body["competitors"]} == {"p-a", "p-b"}
    assert all(c["is_new"] is False for c in latest_body["competitors"])
    assert all(o["is_new"] is False for o in latest_body["opportunities"])
    assert latest_body["draft_post"]["status"] == "draft"
    assert latest_body["meta"]["user_id"] == "owner-a"


def test_latest_sin_analisis_da_404(
    client, configured_db, clean_tables, as_user, create_business
):
    create_business("owner-a")
    as_user("owner-a")
    response = client.get("/api/analysis/latest")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "sin_analisis"


def test_analyze_sin_onboarding_da_409(client, configured_db, clean_tables, as_user):
    as_user("owner-sin-negocio")
    response = client.post("/api/analyze", json=_analyze_body())
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "onboarding_incompleto"


def test_analyze_con_ancla_inexistente_da_404(
    client,
    configured_db,
    clean_tables,
    as_user,
    create_business,
    fake_places,
):
    business = create_business(
        "owner-a", name="Café Inexistente", anchor_place_id="anchor-x"
    )
    fake_places.configure(anchor=None, competitors=[])
    as_user("owner-a")

    response = client.post(
        "/api/analyze",
        json={
            "business_name": "Café Inexistente",
            "business_type": "café",
            "zone": "Palermo Soho",
            "sales_channel": "local",
            "refresh_places": True,
        },
    )
    assert response.status_code == 404
    assert "Verificá" in response.json()["detail"]
    assert _count(configured_db, "app.analisis", business["id"]) == 0


def test_latest_aisla_el_analisis_por_negocio(
    client, configured_db, clean_tables, as_user, create_business
):
    business_a = create_business("owner-a", name="Café A", anchor_place_id="anchor-a")
    business_b = create_business("owner-b", name="Café B", anchor_place_id="anchor-b")

    db.save_analysis_run(
        business_a["id"],
        competitors=[_competitor("p-a", "Café A")],
        opportunities=[],
        clusters=[],
        draft_post=None,
        meta={},
    )
    db.save_analysis_run(
        business_b["id"],
        competitors=[_competitor("p-b", "Café B")],
        opportunities=[],
        clusters=[],
        draft_post=None,
        meta={},
    )

    as_user("owner-a")
    latest_a = client.get("/api/analysis/latest").json()
    assert [c["place_id"] for c in latest_a["competitors"]] == ["p-a"]

    as_user("owner-b")
    latest_b = client.get("/api/analysis/latest").json()
    assert [c["place_id"] for c in latest_b["competitors"]] == ["p-b"]


def test_refresh_ignora_cache_y_el_analisis_normal_la_reutiliza(
    client,
    configured_db,
    clean_tables,
    as_user,
    create_business,
    fake_places,
):
    business = create_business("owner-a")
    as_user("owner-a")

    fake_places.configure(
        anchor=ANCHOR,
        competitors=[COMP_A],
        details={"p-a": DETAILS["p-a"]},
    )
    first = client.post("/api/analyze", json=_analyze_body(refresh_places=True))
    assert first.status_code == 200, first.text
    assert {c["place_id"] for c in first.json()["competitors"]} == {"p-a"}
    assert all(c["cached"] is False for c in first.json()["competitors"])

    fake_places.configure(
        anchor=ANCHOR,
        competitors=[COMP_B],
        details={"p-b": DETAILS["p-b"]},
    )
    cached = client.post("/api/analyze", json=_analyze_body(refresh_places=False))
    assert cached.status_code == 200, cached.text
    assert {c["place_id"] for c in cached.json()["competitors"]} == {"p-a"}
    assert all(c["cached"] is True for c in cached.json()["competitors"])
    assert cached.json()["analysis"]["new_competitors"] == 0

    fresh = client.post("/api/analyze", json=_analyze_body(refresh_places=True))
    assert fresh.status_code == 200, fresh.text
    assert {c["place_id"] for c in fresh.json()["competitors"]} == {"p-b"}
    assert all(c["cached"] is False for c in fresh.json()["competitors"])
    assert fresh.json()["analysis"]["new_competitors"] == 1

    latest = client.get("/api/analysis/latest")
    assert latest.status_code == 200
    latest_body = latest.json()
    assert {c["place_id"] for c in latest_body["competitors"]} == {"p-b"}
    assert latest_body["analysis"]["new_competitors"] == 1
    assert all(c["is_new"] is True for c in latest_body["competitors"])
    assert latest_body["analysis"]["new_opportunities"] >= 1
    assert any(o["is_new"] is True for o in latest_body["opportunities"])

    active = _rows(
        configured_db,
        """
        SELECT place_id,
               (last_seen_run_id = (
                   SELECT id
                     FROM app.analisis
                    WHERE business_id = %(id)s::uuid
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
               )) AS active
          FROM app.competidores
         WHERE business_id = %(id)s::uuid
         ORDER BY place_id
        """,
        {"id": business["id"]},
    )
    assert {row["place_id"]: row["active"] for row in active} == {
        "p-a": False,
        "p-b": True,
    }


def test_none_no_se_marca_como_oportunidad_nueva(
    client, configured_db, clean_tables, as_user, create_business
):
    business = create_business("owner-a")
    db.save_analysis_run(
        business["id"],
        competitors=[],
        opportunities=[
            {
                "key": "category:precios-altos",
                "title": "Dolor rival: precios altos (2 menciones)",
                "evidence": "2 menciones",
                "confidence": "media",
            }
        ],
        clusters=[],
        draft_post=None,
        meta={},
    )
    saved = db.save_analysis_run(
        business["id"],
        competitors=[],
        opportunities=[
            {
                "key": "none",
                "title": "Sin gaps claros en los datos actuales",
                "evidence": "Ningún cluster negativo con volumen suficiente.",
                "confidence": "baja",
            }
        ],
        clusters=[],
        draft_post=None,
        meta={},
    )
    assert saved["new_opportunity_keys"] == []

    as_user("owner-a")
    latest = client.get("/api/analysis/latest")
    assert latest.status_code == 200
    body = latest.json()
    assert body["analysis"]["new_opportunities"] == 0
    assert [o["key"] for o in body["opportunities"]] == ["none"]
    assert body["opportunities"][0]["is_new"] is False


def test_si_falla_el_guardado_no_devuelve_exito(
    client,
    configured_db,
    clean_tables,
    as_user,
    create_business,
    fake_places,
):
    business = create_business("owner-a")
    fake_places.configure(
        anchor=ANCHOR,
        competitors=[COMP_A],
        details={"p-a": DETAILS["p-a"]},
    )
    as_user("owner-a")

    with psycopg.connect(configured_db, autocommit=True) as conn:
        conn.execute(
            """
            CREATE OR REPLACE FUNCTION app._fail_analisis_insert()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'falla inyectada';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        conn.execute("DROP TRIGGER IF EXISTS fail_analisis_insert ON app.analisis")
        conn.execute(
            """
            CREATE TRIGGER fail_analisis_insert
            BEFORE INSERT ON app.analisis
            FOR EACH ROW EXECUTE FUNCTION app._fail_analisis_insert()
            """
        )
    try:
        response = client.post("/api/analyze", json=_analyze_body())
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "analisis_no_guardado"
        assert _count(configured_db, "app.analisis", business["id"]) == 0
        assert _count(configured_db, "app.competidores", business["id"]) == 0
        assert _count(configured_db, "app.oportunidades", business["id"]) == 0
    finally:
        with psycopg.connect(configured_db, autocommit=True) as conn:
            conn.execute("DROP TRIGGER IF EXISTS fail_analisis_insert ON app.analisis")
            conn.execute("DROP FUNCTION IF EXISTS app._fail_analisis_insert()")


def test_reonboarding_invalida_solo_si_cambia_la_identidad(
    client, configured_db, clean_tables, as_user, create_business
):
    business = create_business("owner-a", zone="Palermo Soho")
    db.save_analysis_run(
        business["id"],
        competitors=[_competitor("p-a", "Café A")],
        opportunities=[],
        clusters=[],
        draft_post=None,
        meta={},
    )

    as_user("owner-a")
    assert client.get("/api/analysis/latest").status_code == 200

    create_business("owner-a", zone="Palermo Soho")
    as_user("owner-a")
    assert client.get("/api/analysis/latest").status_code == 200

    create_business("owner-a", zone="Belgrano")
    as_user("owner-a")
    response = client.get("/api/analysis/latest")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "sin_analisis"
    assert _count(configured_db, "app.analisis", business["id"]) == 0
    assert _count(configured_db, "app.competidores", business["id"]) == 0
