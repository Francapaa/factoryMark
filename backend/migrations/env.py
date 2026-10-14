"""Alembic env: solo modo online, upgrade manual explícito.

Uso desde backend/: `uv run alembic upgrade head`.
La URL sale de backend/.env (DATABASE_URL) vía settings — nunca de este
archivo. Sin auto-migrate: el servidor jamás aplica migraciones al arrancar.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from alembic import context

config = context.config


def _engine_url(raw: str) -> str:
    """DATABASE_URL (psycopg) → URL SQLAlchemy con driver psycopg3."""
    url = raw.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    from config import settings

    if not settings.database_url:
        raise RuntimeError("Falta DATABASE_URL en backend/.env")
    engine = create_engine(_engine_url(settings.database_url))
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
