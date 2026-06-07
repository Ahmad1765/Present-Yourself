import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_storage
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Deck, ExportArtifact, Project
from app.schemas.api import ExportIn, ExportOut

router = APIRouter(tags=["exports"])


@router.post("/decks/{deck_id}/export", response_model=ExportOut, status_code=status.HTTP_202_ACCEPTED)
async def kickoff_export(
    deck_id: uuid.UUID,
    payload: ExportIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportOut:
    res = await db.execute(
        select(Deck).join(Project, Project.id == Deck.project_id).where(
            Deck.id == deck_id, Project.user_id == uuid.UUID(user.id)
        )
    )
    deck = res.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")

    artifact = ExportArtifact(deck_id=deck.id, format=payload.format, storage_url="")
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    from app.tasks.export_pptx import export_pptx_task

    export_pptx_task.delay(str(artifact.id))
    return ExportOut.model_validate(artifact)


@router.get("/exports/{artifact_id}", response_model=ExportOut)
async def get_export(
    artifact_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportOut:
    res = await db.execute(
        select(ExportArtifact)
        .join(Deck, Deck.id == ExportArtifact.deck_id)
        .join(Project, Project.id == Deck.project_id)
        .where(ExportArtifact.id == artifact_id, Project.user_id == uuid.UUID(user.id))
    )
    artifact = res.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Export not found")

    # Sign a fresh download URL if the artifact is ready
    if artifact.storage_url and artifact.storage_url.startswith("s3://"):
        storage = get_storage()
        key = artifact.storage_url.removeprefix("s3://").split("/", 1)[1]
        signed = storage.presign_get(key, expires=3600)
        out = ExportOut.model_validate(artifact)
        out.storage_url = signed
        return out
    return ExportOut.model_validate(artifact)
