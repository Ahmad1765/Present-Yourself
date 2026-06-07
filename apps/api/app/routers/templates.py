import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Template
from app.schemas.api import TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateRegisterIn(BaseModel):
    name: str
    storage_key: str


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateOut]:
    res = await db.execute(
        select(Template).where(Template.user_id == uuid.UUID(user.id)).order_by(Template.created_at.desc())
    )
    return [TemplateOut.model_validate(t) for t in res.scalars().all()]


@router.post("", response_model=TemplateOut, status_code=status.HTTP_202_ACCEPTED)
async def register_template(
    payload: TemplateRegisterIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateOut:
    """Client uploaded PPTX to S3 via presigned URL; we now ingest + parse it."""
    template = Template(
        user_id=uuid.UUID(user.id),
        name=payload.name,
        source_pptx_url=payload.storage_key,
        design_tokens={},
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    from app.tasks.template_extract import extract_template_task

    extract_template_task.delay(str(template.id))
    return TemplateOut.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    res = await db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == uuid.UUID(user.id))
    )
    template = res.scalar_one_or_none()
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    await db.delete(template)
    await db.commit()
