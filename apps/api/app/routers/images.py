import asyncio
import uuid

from fastapi import APIRouter, Depends, Query

from app.adapters import get_image_adapter
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.schemas.api import ImageSearchOut, ImageSearchResult
from app.services.keys import resolve_key
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/search", response_model=ImageSearchOut)
async def image_search(
    q: str = Query(..., min_length=1, max_length=120),
    providers: str = Query(default="unsplash,pexels"),
    page: int = Query(default=1, ge=1, le=20),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageSearchOut:
    requested = [p.strip() for p in providers.split(",") if p.strip()]
    tasks = []
    for provider in requested:
        try:
            key = await resolve_key(db, uuid.UUID(user.id), provider)
        except ValueError:
            continue
        adapter = get_image_adapter(provider, key)
        tasks.append(adapter.search(q, page=page))

    if not tasks:
        return ImageSearchOut(results=[], next_page=None)

    batches = await asyncio.gather(*tasks, return_exceptions=True)
    merged: list[ImageSearchResult] = []
    seen: set[str] = set()
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            merged.append(ImageSearchResult(**item))
    return ImageSearchOut(results=merged, next_page=page + 1 if merged else None)
