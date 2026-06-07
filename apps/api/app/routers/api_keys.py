import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.crypto import encrypt_key
from app.db import get_db
from app.models import UserApiKey
from app.schemas.api import ApiKeyIn, ApiKeyOut

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyOut])
async def list_keys(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyOut]:
    res = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == uuid.UUID(user.id)).order_by(UserApiKey.created_at)
    )
    rows = res.scalars().all()
    return [
        ApiKeyOut(
            provider=row.provider,  # type: ignore[arg-type]
            fingerprint=row.key_fingerprint,
            last_used_at=row.last_used_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("", response_model=ApiKeyOut, status_code=status.HTTP_201_CREATED)
async def upsert_key(
    payload: ApiKeyIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyOut:
    ct, nonce, fp = encrypt_key(payload.key, payload.provider)
    res = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == uuid.UUID(user.id),
            UserApiKey.provider == payload.provider,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = UserApiKey(
            user_id=uuid.UUID(user.id),
            provider=payload.provider,
            key_ciphertext=ct,
            key_nonce=nonce,
            key_fingerprint=fp,
        )
        db.add(row)
    else:
        row.key_ciphertext = ct
        row.key_nonce = nonce
        row.key_fingerprint = fp
    await db.commit()
    await db.refresh(row)
    return ApiKeyOut(
        provider=row.provider,  # type: ignore[arg-type]
        fingerprint=row.key_fingerprint,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    provider: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    res = await db.execute(
        delete(UserApiKey).where(
            UserApiKey.user_id == uuid.UUID(user.id),
            UserApiKey.provider == provider,
        )
    )
    if res.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Key not found")
    await db.commit()
