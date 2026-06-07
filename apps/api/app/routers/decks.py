import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth import CurrentUser, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import Deck, DeckVersion, GenerationJob, Project
from app.schemas.api import DeckOut, DeckPatch, GenerationSettings, SlideRegenerateIn

router = APIRouter(tags=["decks"])


@router.post(
    "/projects/{project_id}/decks",
    response_model=DeckOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def kickoff_generation(
    project_id: uuid.UUID,
    payload: GenerationSettings,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeckOut:
    project = await _load_project(db, project_id, user.id)
    deck = Deck(
        project_id=project.id,
        status="queued",
        slide_count=payload.slide_count,
        blueprint={},
        generation_meta={"settings": payload.model_dump(mode="json")},
    )
    db.add(deck)
    await db.flush()
    job = GenerationJob(deck_id=deck.id, stage="queued")
    db.add(job)
    await db.commit()
    await db.refresh(deck)

    # Lazy import to keep web boot independent of Celery
    from app.tasks.generate import generate_deck

    task = generate_deck.delay(str(deck.id), str(user.id), payload.model_dump(mode="json"))
    job.celery_task_id = task.id
    await db.commit()
    return DeckOut.model_validate(deck)


@router.get("/decks/{deck_id}", response_model=DeckOut)
async def get_deck(
    deck_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeckOut:
    deck = await _load_deck(db, deck_id, user.id)
    return DeckOut.model_validate(deck)


@router.patch("/decks/{deck_id}", response_model=DeckOut)
async def save_blueprint(
    deck_id: uuid.UUID,
    payload: DeckPatch,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeckOut:
    deck = await _load_deck(db, deck_id, user.id)
    # Snapshot prior state
    db.add(DeckVersion(deck_id=deck.id, blueprint=deck.blueprint, label="auto-save", author=uuid.UUID(user.id)))
    deck.blueprint = payload.blueprint.model_dump(mode="json")
    await db.commit()
    await db.refresh(deck)
    return DeckOut.model_validate(deck)


@router.post("/decks/{deck_id}/slides/{idx}/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_slide(
    deck_id: uuid.UUID,
    idx: int,
    payload: SlideRegenerateIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    deck = await _load_deck(db, deck_id, user.id)
    from app.tasks.generate import regenerate_slide_task

    task = regenerate_slide_task.delay(str(deck.id), str(user.id), idx, payload.hint)
    return {"deck_id": str(deck.id), "task_id": task.id}


@router.get("/decks/{deck_id}/stream")
async def stream_progress(
    deck_id: uuid.UUID,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    await _load_deck(db, deck_id, user.id)  # auth + existence
    settings = get_settings()
    channel = f"job:{deck_id}"

    async def event_gen():
        client = aioredis.from_url(settings.redis_url)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        try:
            # Replay last known state if any
            last = await client.get(f"{channel}:last")
            if last:
                yield {"event": "state", "data": last.decode()}
            while True:
                if await request.is_disconnected():
                    break
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15)
                if msg is None:
                    yield {"event": "ping", "data": "{}"}
                    continue
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield {"event": "state", "data": data}
                try:
                    parsed = json.loads(data)
                    if parsed.get("stage") in ("ready", "failed"):
                        break
                except Exception:  # noqa: BLE001
                    pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await client.close()
            await asyncio.sleep(0)

    return EventSourceResponse(event_gen())


async def _load_project(db: AsyncSession, project_id: uuid.UUID, user_id: str) -> Project:
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == uuid.UUID(user_id))
    )
    project = res.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


async def _load_deck(db: AsyncSession, deck_id: uuid.UUID, user_id: str) -> Deck:
    res = await db.execute(
        select(Deck).join(Project, Project.id == Deck.project_id).where(
            Deck.id == deck_id, Project.user_id == uuid.UUID(user_id)
        )
    )
    deck = res.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    return deck
