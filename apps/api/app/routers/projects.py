import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Deck, Project
from app.schemas.api import ProjectIn, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=24, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    stmt = select(Project).where(Project.user_id == uuid.UUID(user.id))
    if q:
        stmt = stmt.where(Project.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(Project.updated_at.desc()).offset((page - 1) * limit).limit(limit)
    res = await db.execute(stmt)
    return [ProjectOut.model_validate(p) for p in res.scalars().all()]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = Project(
        user_id=uuid.UUID(user.id),
        title=payload.title,
        topic=payload.topic,
        brief=payload.brief,
        language=payload.language,
        template_id=payload.template_id,
        default_settings=payload.default_settings,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await _load(db, project_id, user.id)
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await _load(db, project_id, user.id)
    for field in ("title", "topic", "brief", "language", "template_id", "default_settings"):
        setattr(project, field, getattr(payload, field))
    await db.commit()
    await db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    project = await _load(db, project_id, user.id)
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/duplicate", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def duplicate_project(
    project_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    original = await _load(db, project_id, user.id)
    clone = Project(
        user_id=uuid.UUID(user.id),
        title=f"{original.title} (copy)",
        topic=original.topic,
        brief=original.brief,
        language=original.language,
        template_id=original.template_id,
        default_settings=original.default_settings,
    )
    db.add(clone)
    await db.commit()
    await db.refresh(clone)
    return ProjectOut.model_validate(clone)


async def _load(db: AsyncSession, project_id: uuid.UUID, user_id: str) -> Project:
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == uuid.UUID(user_id))
    )
    project = res.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project
