"""Clerk JWT verification with JWKS caching.

Falls back to a dev bypass mode when CLERK_JWKS_URL is empty and env != 'prod',
so local development works without a Clerk account. The bypass accepts the
header `X-Dev-User-Id` and creates/returns that user row.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import AppUser

_JWKS_CACHE: dict[str, tuple[float, dict]] = {}
_JWKS_TTL = 3600.0


@dataclass
class CurrentUser:
    id: str
    clerk_id: str
    email: str


async def _fetch_jwks(url: str) -> dict:
    now = time.time()
    cached = _JWKS_CACHE.get(url)
    if cached and now - cached[0] < _JWKS_TTL:
        return cached[1]
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    _JWKS_CACHE[url] = (now, data)
    return data


async def _verify_clerk_token(token: str) -> tuple[str, str]:
    settings = get_settings()
    if not settings.clerk_jwks_url or not settings.clerk_audience:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Clerk not configured (CLERK_JWKS_URL and CLERK_AUDIENCE required)",
        )
    jwks = await _fetch_jwks(settings.clerk_jwks_url)
    unverified = jwt.get_unverified_header(token)
    key = next((k for k in jwks["keys"] if k["kid"] == unverified["kid"]), None)
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown signing key")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.clerk_audience,
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    return claims["sub"], claims.get("email", "")


async def _upsert_user(db: AsyncSession, clerk_id: str, email: str) -> AppUser:
    res = await db.execute(select(AppUser).where(AppUser.clerk_user_id == clerk_id))
    user = res.scalar_one_or_none()
    if user is None:
        user = AppUser(clerk_user_id=clerk_id, email=email or f"{clerk_id}@example.invalid")
        db.add(user)
        await db.flush()
    elif email and user.email != email:
        user.email = email
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> CurrentUser:
    settings = get_settings()

    if settings.env != "prod" and not settings.clerk_jwks_url and x_dev_user_id:
        user = await _upsert_user(db, x_dev_user_id, f"{x_dev_user_id}@dev.local")
        return CurrentUser(id=str(user.id), clerk_id=user.clerk_user_id, email=user.email)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    clerk_id, email = await _verify_clerk_token(token)
    user = await _upsert_user(db, clerk_id, email)
    return CurrentUser(id=str(user.id), clerk_id=user.clerk_user_id, email=user.email)
