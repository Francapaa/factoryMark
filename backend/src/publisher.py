"""Publisher mock: genera borradores y registra aprobación humana.

Wave 3: publicación real vía Meta Graph API / LinkedIn API detrás de
`PUBLISH_ENABLED`. En esta wave todo queda en `draft` hasta aprobación.
"""

from __future__ import annotations

from state import DraftPost

# Feature flag: Wave 3 lo pone en True con OAuth configurado.
PUBLISH_ENABLED = False


def build_draft(opportunity_title: str, brand: dict) -> DraftPost:
    tone = brand.get("tone", "cercano")
    handle = brand.get("handle", "")
    name = brand.get("name", "nuestro local")
    copy_text = (
        f"{name} te escucha: {opportunity_title}. "
        f"Vení a comprobarlo hoy mismo {handle}".strip()
        + f" (tono: {tone})"
    )
    hashtags = ["#consumelocal", "#barrio"]
    return DraftPost(copy_text=copy_text, hashtags=hashtags, status="draft")


def set_status(draft: DraftPost, approved: bool) -> DraftPost:
    data = draft.model_dump()
    data["status"] = "approved" if approved else "rejected"
    return DraftPost(**data)
