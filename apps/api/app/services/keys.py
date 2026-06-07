"""Resolve a provider's API key for a given user.

Order of resolution:
1. User's stored key (encrypted) for that provider.
2. System default key from environment (if configured).
3. Raise ValueError — caller surfaces as 4xx to the user.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import decrypt_key
from app.models import UserApiKey


_SYSTEM_FALLBACKS = {
    "openai":    lambda s: s.system_openai_key,
    "anthropic": lambda s: s.system_anthropic_key,
    "gemini":    lambda s: s.system_gemini_key,
    "tavily":    lambda s: s.system_tavily_key,
    "unsplash":  lambda s: s.system_unsplash_key,
    "pexels":    lambda s: s.system_pexels_key,
    "pixabay":   lambda s: s.system_pixabay_key,
    "stability": lambda s: s.system_stability_key,
}


async def resolve_key(db: AsyncSession, user_id: uuid.UUID, provider: str) -> str:
    res = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.provider == provider)
    )
    row = res.scalar_one_or_none()
    if row is not None:
        return decrypt_key(row.key_ciphertext, row.key_nonce, provider)

    settings = get_settings()
    fallback = _SYSTEM_FALLBACKS.get(provider, lambda _: "")
    val = fallback(settings)
    if val:
        return val
    raise ValueError(f"No API key configured for provider: {provider}")
