"""End-to-end deck generation orchestrator."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.adapters import get_image_adapter, get_llm_adapter, get_research_adapter
from app.config import get_settings
from app.models import Deck, GenerationJob, Project, Template
from app.schemas.slide import SlideBlueprint
from app.services.keys import resolve_key
from app.tasks._helpers import db_session, publish_progress
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.generate.generate_deck", bind=True, max_retries=1)
def generate_deck(self, deck_id: str, user_id: str, settings: dict) -> dict:
    return asyncio.run(_generate_deck_async(deck_id, user_id, settings))


async def _generate_deck_async(deck_id: str, user_id: str, settings: dict) -> dict:
    publish_progress(deck_id, "researching", 5)
    started = datetime.now(timezone.utc)

    with db_session() as db:
        deck = db.get(Deck, uuid.UUID(deck_id))
        if deck is None:
            return {"ok": False, "error": "deck not found"}
        project = db.get(Project, deck.project_id)
        template = db.get(Template, project.template_id) if project.template_id else None
        design_tokens = template.design_tokens if template else None

        job = db.execute(
            select(GenerationJob).where(GenerationJob.deck_id == deck.id)
        ).scalar_one_or_none()
        if job is not None:
            job.stage = "researching"
            job.started_at = started

        topic = project.topic
        brief = project.brief
        language = project.language

    try:
        # 1. Research
        research_query = topic if not brief else f"{topic} — {brief}"
        try:
            tavily_key = await _resolve_key_async(user_id, "tavily")
            research_adapter = get_research_adapter("tavily", tavily_key)
            research = await research_adapter.search(research_query, max_results=8)
        except ValueError:
            research = []  # no key → proceed without research
        publish_progress(deck_id, "writing", 30, sources=len(research))

        # 2. LLM authoring
        provider = settings.get("model_provider", "openai")
        llm_key = await _resolve_key_async(user_id, provider)
        llm = get_llm_adapter(provider, llm_key)
        blueprint = await llm.author_blueprint(
            topic=topic,
            brief=brief,
            research=[dict(r) for r in research],
            slide_count=settings.get("slide_count", 10),
            language=language,
            tone=settings.get("tone"),
            audience=settings.get("audience"),
            design_tokens=design_tokens,
        )
        publish_progress(deck_id, "imaging", 60)

        # 3. Image fetch — fan out across image slides
        if settings.get("with_images", True):
            blueprint = await _attach_images(blueprint, user_id, settings.get("image_providers", ["unsplash", "pexels"]))
        publish_progress(deck_id, "polishing", 90)

        # 4. Persist
        with db_session() as db:
            deck = db.get(Deck, uuid.UUID(deck_id))
            deck.blueprint = blueprint.model_dump(mode="json")
            deck.research_brief = {"items": [dict(r) for r in research]}
            deck.status = "ready"
            deck.generation_meta = {
                **(deck.generation_meta or {}),
                "provider": provider,
                "duration_sec": (datetime.now(timezone.utc) - started).total_seconds(),
            }
            job = db.execute(
                select(GenerationJob).where(GenerationJob.deck_id == deck.id)
            ).scalar_one_or_none()
            if job is not None:
                job.stage = "ready"
                job.progress_pct = 100
                job.finished_at = datetime.now(timezone.utc)

        publish_progress(deck_id, "ready", 100)
        return {"ok": True, "deck_id": deck_id}

    except Exception as exc:  # noqa: BLE001
        with db_session() as db:
            deck = db.get(Deck, uuid.UUID(deck_id))
            deck.status = "failed"
            deck.generation_meta = {**(deck.generation_meta or {}), "error": str(exc)}
            job = db.execute(
                select(GenerationJob).where(GenerationJob.deck_id == deck.id)
            ).scalar_one_or_none()
            if job is not None:
                job.stage = "failed"
                job.error = str(exc)
                job.finished_at = datetime.now(timezone.utc)
        publish_progress(deck_id, "failed", 100, error=str(exc))
        raise


@celery_app.task(name="app.tasks.generate.regenerate_slide_task")
def regenerate_slide_task(deck_id: str, user_id: str, slide_index: int, hint: str | None) -> dict:
    return asyncio.run(_regenerate_slide_async(deck_id, user_id, slide_index, hint))


async def _regenerate_slide_async(deck_id: str, user_id: str, slide_index: int, hint: str | None) -> dict:
    with db_session() as db:
        deck = db.get(Deck, uuid.UUID(deck_id))
        if deck is None or not deck.blueprint:
            return {"ok": False, "error": "deck not ready"}
        existing = SlideBlueprint.model_validate(deck.blueprint)

    provider = (deck.generation_meta or {}).get("provider", "openai")
    key = await _resolve_key_async(user_id, provider)
    llm = get_llm_adapter(provider, key)
    # naive approach: ask for a full deck of size 1 keyed to the same topic + hint
    project_topic = existing.deck.title
    new_blueprint = await llm.author_blueprint(
        topic=project_topic,
        brief=f"Regenerate ONLY slide index {slide_index}. Hint: {hint or '-'}",
        research=[],
        slide_count=len(existing.deck.slides),
        language=existing.deck.language,
        tone=None,
        audience=None,
        design_tokens=existing.deck.design_tokens.model_dump(mode="json"),
    )
    if 0 <= slide_index < len(new_blueprint.deck.slides):
        merged = existing.model_copy(deep=True)
        merged.deck.slides[slide_index] = new_blueprint.deck.slides[slide_index]
        with db_session() as db:
            deck = db.get(Deck, uuid.UUID(deck_id))
            deck.blueprint = merged.model_dump(mode="json")
        return {"ok": True}
    return {"ok": False, "error": "slide_index out of range"}


async def _attach_images(blueprint: SlideBlueprint, user_id: str, providers: list[str]) -> SlideBlueprint:
    keys: dict[str, str] = {}
    for p in providers:
        try:
            keys[p] = await _resolve_key_async(user_id, p)
        except ValueError:
            continue

    if not keys:
        return blueprint

    async def fetch_for_slide(slide):
        for el in slide.elements:
            if el.kind != "image":
                continue
            query = el.alt or " ".join(
                t.content for t in slide.elements if t.kind == "text" and t.content
            )[:120]
            for provider, api_key in keys.items():
                try:
                    adapter = get_image_adapter(provider, api_key)
                    results = await adapter.search(query, per_page=4)
                except Exception:  # noqa: BLE001
                    continue
                if results:
                    el.source = {
                        "provider": provider,
                        "url": results[0]["url"],
                        "credit": results[0]["credit"],
                    }
                    el.candidates = [{"url": r["url"], "credit": r["credit"]} for r in results[1:]]
                    break

    await asyncio.gather(*(fetch_for_slide(s) for s in blueprint.deck.slides))
    return blueprint


async def _resolve_key_async(user_id: str, provider: str) -> str:
    """Wrap sync key resolution in a thread for use from async code (Celery task is sync top-level)."""
    # Use sync session because we're inside Celery; just import system fallback directly when no DB row.
    from app.models import UserApiKey
    from app.crypto import decrypt_key

    with db_session() as db:
        row = db.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == uuid.UUID(user_id),
                UserApiKey.provider == provider,
            )
        ).scalar_one_or_none()
        if row is not None:
            return decrypt_key(row.key_ciphertext, row.key_nonce, provider)

    settings = get_settings()
    fallbacks = {
        "openai": settings.system_openai_key,
        "anthropic": settings.system_anthropic_key,
        "gemini": settings.system_gemini_key,
        "tavily": settings.system_tavily_key,
        "unsplash": settings.system_unsplash_key,
        "pexels": settings.system_pexels_key,
        "pixabay": settings.system_pixabay_key,
    }
    val = fallbacks.get(provider, "")
    if val:
        return val
    raise ValueError(f"No API key configured for provider: {provider}")
