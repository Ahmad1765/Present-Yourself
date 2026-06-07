"""Export a Deck blueprint as PPTX to object storage."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.adapters import get_storage
from app.models import Deck, ExportArtifact
from app.schemas.slide import SlideBlueprint
from app.services.pptx_render import render_blueprint
from app.tasks._helpers import db_session
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.export_pptx.export_pptx_task", bind=True, max_retries=2)
def export_pptx_task(self, artifact_id: str) -> dict:
    with db_session() as db:
        artifact = db.get(ExportArtifact, uuid.UUID(artifact_id))
        if artifact is None:
            return {"ok": False, "error": "artifact not found"}
        deck = db.get(Deck, artifact.deck_id)
        if deck is None or not deck.blueprint:
            return {"ok": False, "error": "deck not ready"}
        blueprint = SlideBlueprint.model_validate(deck.blueprint)

    pptx_bytes = render_blueprint(blueprint)
    storage = get_storage()
    key = storage.new_key(f"exports/{deck.id}", "pptx")
    storage.put_object(
        key,
        pptx_bytes,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

    with db_session() as db:
        artifact = db.get(ExportArtifact, uuid.UUID(artifact_id))
        if artifact is None:
            # Artifact row was deleted between sessions (race or cleanup); object is uploaded
            # but no DB row to update. Return failure so the caller can retry/repair.
            return {"ok": False, "error": "artifact deleted during export", "uploaded_key": key}
        artifact.storage_url = f"s3://{storage.bucket}/{key}"
        artifact.size_bytes = len(pptx_bytes)
        artifact.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    return {"ok": True, "size": len(pptx_bytes)}
