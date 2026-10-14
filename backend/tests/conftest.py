"""Fixtures compartidas: integración-first, sin slop.

- Auth desactivada vía fixture (no global).
- Cache de Places/Tavily siempre en tmp_path (nunca backend/data/cache).
- Borde HTTP solo con httpx.MockTransport.
- DB real cuando hay DATABASE_URL; si no, los tests que la requieren hacen skip.
"""

from __future__ import annotations

import os

import httpx
import pytest

REQUIRES_DB = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="requiere Postgres efímera (DATABASE_URL)"
)


@pytest.fixture
def auth_disabled(monkeypatch):
    """Dev-mode: user fijo dev-user. Restaurado al salir."""
    from config import settings

    old = settings.auth_disabled
    settings.auth_disabled = True
    yield "dev-user"
    settings.auth_disabled = old


@pytest.fixture
def isolated_cache(monkeypatch, tmp_path):
    """Redirige default_cache_dir de places/tavily a tmp_path."""
    import tools.places as places_mod
    from tools import tavily as tavily_mod

    monkeypatch.setattr(places_mod, "default_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(tavily_mod, "default_cache_dir", lambda: tmp_path)
    return tmp_path


def mock_transport(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def db_isolated():
    """Limpia las tablas del owner de test si hay DB. Sin DB: skip explícito."""
    if not os.getenv("DATABASE_URL"):
        pytest.skip("requiere Postgres efímera (DATABASE_URL)")
    import psycopg

    owners = ("dev-user", "user-a", "user-b", "user-1", "owner-test", "owner-e2e")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        for table in ("app.publicaciones", "app.instagram_conexiones", "app.negocios"):
            try:
                cur.execute(
                    f"DELETE FROM {table} WHERE owner_id = ANY(%s)", (list(owners),)
                )
            except Exception:  # noqa: BLE001 - tabla puede no existir en DB efímera
                conn.rollback()
            else:
                conn.commit()
    yield
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        for table in ("app.publicaciones", "app.instagram_conexiones", "app.negocios"):
            try:
                cur.execute(
                    f"DELETE FROM {table} WHERE owner_id = ANY(%s)", (list(owners),)
                )
            except Exception:  # noqa: BLE001 - limpieza best-effort
                conn.rollback()
            else:
                conn.commit()
