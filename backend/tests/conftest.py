"""Fixtures de integración: Postgres real y solo HTTP externo simulado.

La base de test sale de TEST_DATABASE_URL. Nunca se usa DATABASE_URL de
producción: si ambas URLs apuntan al mismo host y base, la suite falla.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx
import psycopg
import pytest
import respx
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from auth import CurrentUser, get_current_user
from config import settings
from main import app
from tools.places import PLACES_SEARCH_URL

_TEST_TABLES = (
    "app.analisis",
    "app.competidores",
    "app.oportunidades",
    "app.negocios",
    "app.instagram_conexiones",
    "app.publicaciones",
)


def _same_database(test_url: str) -> bool:
    production = settings.database_url.strip()
    if not production:
        return False
    prod = urlparse(production)
    test = urlparse(test_url)
    return (
        bool(test.hostname)
        and prod.hostname == test.hostname
        and prod.path.rstrip("/") == test.path.rstrip("/")
    )


@pytest.fixture(scope="session")
def configured_db() -> str:
    url = settings.test_database_url.strip()
    if not url:
        pytest.skip("Falta TEST_DATABASE_URL (rama/base Postgres separada para tests)")
    if not urlparse(url).path.strip("/"):
        pytest.fail("TEST_DATABASE_URL no incluye una base de datos")
    if _same_database(url):
        pytest.fail("TEST_DATABASE_URL apunta a la misma base que DATABASE_URL")

    previous = settings.database_url
    settings.database_url = url
    cfg = Config()
    cfg.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    command.upgrade(cfg, "head")
    try:
        yield url
    finally:
        settings.database_url = previous


def _truncate(url: str) -> None:
    with psycopg.connect(url) as conn:
        conn.execute(f"TRUNCATE {', '.join(_TEST_TABLES)} RESTART IDENTITY CASCADE")
        conn.commit()


@pytest.fixture
def clean_tables(configured_db: str) -> None:
    _truncate(configured_db)
    try:
        yield
    finally:
        _truncate(configured_db)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def as_user():
    def _as(user_id: str) -> None:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=user_id)

    yield _as
    app.dependency_overrides.clear()


@pytest.fixture
def create_business(client: TestClient, as_user):
    def _create(owner_id: str = "owner-a", **overrides) -> dict:
        as_user(owner_id)
        payload = {
            "name": "Café Test",
            "business_type": "café de especialidad",
            "sales_channel": "local",
            "zone": "Palermo Soho",
            "anchor_place_id": "anchor-1",
            "anchor_snapshot": {"address": "Calle Test 123", "rating": 4.5},
        }
        payload.update(overrides)
        response = client.post("/api/businesses", json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    return _create


class FakePlaces:
    def __init__(self) -> None:
        self.anchor: dict | None = None
        self.competitors: list[dict] = []
        self.details: dict[str, dict] = {}
        self.queries: list[str] = []

    def configure(
        self,
        *,
        anchor: dict | None,
        competitors: list[dict],
        details: dict[str, dict] | None = None,
    ) -> None:
        self.anchor = anchor
        self.competitors = competitors
        self.details = details or {}
        self.queries = []

    def search(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        query = str(body.get("textQuery", ""))
        self.queries.append(query)
        if "," in query:
            places = [self.anchor] if self.anchor else []
        else:
            places = ([self.anchor] if self.anchor else []) + self.competitors
        return httpx.Response(200, json={"places": places})

    def place_details(self, request: httpx.Request) -> httpx.Response:
        place_id = request.url.path.rstrip("/").split("/")[-1]
        return httpx.Response(200, json=self.details.get(place_id, {}))


@pytest.fixture
def fake_places(monkeypatch, tmp_path: Path) -> FakePlaces:
    monkeypatch.setattr(settings, "google_places_api_key", "test-key")
    monkeypatch.setattr(settings, "tavily_api_key", "")
    monkeypatch.setattr(settings, "tavily_enabled", False)
    monkeypatch.setattr(settings, "places_cache_dir", str(tmp_path))

    fake = FakePlaces()
    with respx.mock(assert_all_called=False) as router:
        router.post(PLACES_SEARCH_URL).mock(side_effect=fake.search)
        router.get(
            url__regex=r"https://places\.googleapis\.com/v1/places/[^/?]+(?:\?.*)?$"
        ).mock(side_effect=fake.place_details)

        def unexpected(request: httpx.Request):
            raise AssertionError(f"HTTP inesperado: {request.method} {request.url}")

        router.route().mock(side_effect=unexpected)
        yield fake
