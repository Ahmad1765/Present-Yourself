"""HTTP request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.slide import DesignTokens, SlideBlueprint

Provider = Literal[
    "openai", "anthropic", "gemini", "tavily", "unsplash", "pexels", "pixabay", "stability"
]


class ApiKeyIn(BaseModel):
    provider: Provider
    key: str = Field(min_length=8, max_length=512)


class ApiKeyOut(BaseModel):
    provider: Provider
    fingerprint: str
    last_used_at: datetime | None = None
    created_at: datetime


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    topic: str = Field(min_length=1)
    brief: str | None = None
    language: str = "en"
    template_id: uuid.UUID | None = None
    default_settings: dict = Field(default_factory=dict)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    topic: str
    brief: str | None
    language: str
    template_id: uuid.UUID | None
    default_settings: dict
    created_at: datetime
    updated_at: datetime


class GenerationSettings(BaseModel):
    slide_count: int = Field(default=10, ge=3, le=30)
    with_images: bool = True
    model_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    image_providers: list[Literal["unsplash", "pexels", "pixabay"]] = Field(
        default_factory=lambda: ["unsplash", "pexels"]
    )
    template_id: uuid.UUID | None = None
    hints: str | None = None
    tone: str | None = None
    audience: str | None = None


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    slide_count: int
    blueprint: dict
    generation_meta: dict
    created_at: datetime
    updated_at: datetime


class DeckPatch(BaseModel):
    blueprint: SlideBlueprint
    label: str | None = None


class SlideRegenerateIn(BaseModel):
    hint: str | None = None


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    design_tokens: dict
    thumbnail_url: str | None
    created_at: datetime


class ExportIn(BaseModel):
    format: Literal["pptx"] = "pptx"


class ExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    deck_id: uuid.UUID
    format: str
    storage_url: str | None
    size_bytes: int | None
    expires_at: datetime | None
    created_at: datetime


class UploadSignIn(BaseModel):
    purpose: Literal["template", "image"]
    content_type: str
    size: int


class UploadSignOut(BaseModel):
    upload_url: str
    storage_key: str
    expires_in: int


class ImageSearchResult(BaseModel):
    provider: str
    url: str
    thumb_url: str
    credit: str
    width: int | None = None
    height: int | None = None


class ImageSearchOut(BaseModel):
    results: list[ImageSearchResult]
    next_page: int | None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


# Forward references for DesignTokens (already declared in slide.py)
__all__ = [
    "ApiKeyIn",
    "ApiKeyOut",
    "ProjectIn",
    "ProjectOut",
    "GenerationSettings",
    "DeckOut",
    "DeckPatch",
    "SlideRegenerateIn",
    "TemplateOut",
    "ExportIn",
    "ExportOut",
    "UploadSignIn",
    "UploadSignOut",
    "ImageSearchOut",
    "ImageSearchResult",
    "ErrorBody",
    "ErrorResponse",
    "DesignTokens",
]
