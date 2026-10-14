"""Migraciones Alembic: historia lineal con un solo head (offline, sin DB)."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _scripts() -> ScriptDirectory:
    cfg = Config()
    cfg.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    return ScriptDirectory.from_config(cfg)


def test_un_solo_head():
    assert len(_scripts().get_heads()) == 1


def test_baseline_es_raiz_y_lineal():
    revs = list(_scripts().walk_revisions())
    assert revs, "sin revisiones"
    assert revs[-1].down_revision is None
    assert revs[-1].revision == "0001_baseline"
