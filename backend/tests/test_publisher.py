"""Tests publisher mock + endpoint /api/approve. Cero red."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from config import settings
from main import app
from publisher import PUBLISH_ENABLED, build_draft, set_status

client = TestClient(app)


def test_build_draft_usa_brand_kit():
    brand = {"name": "Café Ejemplo", "tone": "cercano y barrial", "handle": "@cafe.ejemplo"}
    draft = build_draft("horario de tarde libre", brand)
    assert draft.status == "draft"
    assert "Café Ejemplo" in draft.copy_text
    assert len(draft.hashtags) > 0
    assert PUBLISH_ENABLED is False


def test_set_status_transitions():
    draft = build_draft("x", {})
    assert set_status(draft, True).status == "approved"
    assert set_status(draft, False).status == "rejected"


def test_approve_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "auth_disabled", True)
    r = client.post("/api/approve", json={"approved": True})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    r = client.post("/api/approve", json={"approved": False})
    assert r.status_code == 200 and r.json()["status"] == "rejected"


def test_golden_set_valido():
    cases = json.loads((Path(__file__).resolve().parents[2] / "eval" / "golden_set.json").read_text(encoding="utf-8"))
    assert len(cases) == 5
    for c in cases:
        assert {"id", "business_type", "zone", "expected_insight"} <= set(c)
