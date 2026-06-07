"""Canonical SlideBlueprint schema. Mirrored by Zod in apps/web/lib/schema.ts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SlideType = Literal[
    "title",
    "section_header",
    "bullet_list",
    "two_column",
    "image_caption",
    "quote",
    "stat_callout",
    "comparison_table",
    "chart_placeholder",
    "closing",
]

ElementKind = Literal["text", "bullets", "image", "shape", "table", "chart_placeholder"]


class TextStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    size: int | None = None
    color: str | None = None  # token name or hex
    align: Literal["left", "center", "right"] | None = None
    weight: int | None = None
    italic: bool = False


class Element(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: ElementKind
    role: str | None = None  # title|subtitle|body|caption|...
    content: str | None = None
    items: list[str] | None = None
    style: TextStyle | None = None
    # image-only fields
    source: dict | None = None  # {provider, url, credit}
    candidates: list[dict] | None = None
    alt: str | None = None


class Slide(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: SlideType
    layout_hint: str | None = None
    elements: list[Element]
    notes: str | None = None
    citations: list[str] = Field(default_factory=list)


class Palette(BaseModel):
    model_config = ConfigDict(extra="forbid")
    background: str = "#FFFFFF"
    foreground: str = "#0F172A"
    accent1: str = "#2563EB"
    accent2: str = "#0EA5E9"
    accent3: str = "#F59E0B"
    muted: str = "#64748B"


class FontSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    family: str = "Inter"
    weight: int = 400


class Fonts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    heading: FontSpec = Field(default_factory=lambda: FontSpec(weight=700))
    body: FontSpec = Field(default_factory=FontSpec)


class Dimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    width_emu: int = 12192000  # 16:9 default
    height_emu: int = 6858000
    aspect: Literal["16:9", "4:3", "16:10"] = "16:9"


class LogoSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-right"


class DesignTokens(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dimensions: Dimensions = Field(default_factory=Dimensions)
    palette: Palette = Field(default_factory=Palette)
    fonts: Fonts = Field(default_factory=Fonts)
    logo: LogoSpec | None = None


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    url: str
    title: str
    publisher: str | None = None
    snippet: str | None = None
    fetched_at: datetime | None = None


class Deck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    language: str = "en"
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    slides: list[Slide]
    citations: list[Citation] = Field(default_factory=list)


class SlideBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    deck: Deck
