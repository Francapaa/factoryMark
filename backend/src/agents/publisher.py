"""Publisher: deja el draft listo para aprobación humana (sin publicar).

Human-in-the-loop: el estado queda en `draft` hasta que alguien lo apruebe
vía `POST /api/approve`. `PUBLISH_ENABLED` sigue en False.
"""

from __future__ import annotations

from publisher import DraftPost


def publisher_node(state: dict) -> dict:
    pending = DraftPost(**state["draft_post"])
    assert pending.status == "draft"  # sale pendiente de aprobación humana
    return {"draft_post": pending.model_dump(mode="json"), "trace": ["publisher"]}
