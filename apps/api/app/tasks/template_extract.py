"""Parse uploaded PPTX → extract design_tokens + thumbnail."""

from __future__ import annotations

import io
import uuid

from PIL import Image

from app.adapters import get_storage
from app.models import Template
from app.services.template_extract import extract_design_tokens
from app.tasks._helpers import db_session
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.template_extract.extract_template_task", bind=True, max_retries=2)
def extract_template_task(self, template_id: str) -> dict:
    with db_session() as db:
        template = db.get(Template, uuid.UUID(template_id))
        if template is None:
            return {"ok": False, "error": "template not found"}
        storage_key = template.source_pptx_url

    storage = get_storage()
    pptx_bytes = storage.get_object(storage_key)
    tokens = extract_design_tokens(pptx_bytes)

    # Best-effort thumbnail (palette swatch). Real-world: render with LibreOffice headless.
    thumb_key = storage_key.rsplit(".", 1)[0] + "_thumb.png"
    storage.put_object(thumb_key, _palette_thumbnail(tokens), "image/png")

    with db_session() as db:
        template = db.get(Template, uuid.UUID(template_id))
        template.design_tokens = tokens
        template.thumbnail_url = f"s3://{storage.bucket}/{thumb_key}"
    return {"ok": True}


def _palette_thumbnail(tokens: dict) -> bytes:
    palette = tokens.get("palette", {}) if isinstance(tokens, dict) else {}
    background = palette.get("background", "#FFFFFF") if isinstance(palette, dict) else "#FFFFFF"
    try:
        bg_color = _hex(background)
    except Exception:  # noqa: BLE001
        bg_color = (255, 255, 255)
    img = Image.new("RGB", (256, 144), bg_color)
    keys = ["accent1", "accent2", "accent3", "foreground"]
    swatch_w = 256 // len(keys)
    for i, k in enumerate(keys):
        value = palette.get(k, "#000000") if isinstance(palette, dict) else "#000000"
        try:
            color = _hex(value)
        except Exception:  # noqa: BLE001
            color = (0, 0, 0)
        for x in range(i * swatch_w, (i + 1) * swatch_w):
            for y in range(80, 144):
                img.putpixel((x, y), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _hex(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise ValueError("hex value must be a string")
    v = value.lstrip("#")
    if len(v) != 6:
        raise ValueError(f"hex value must be 6 chars, got {len(v)}")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
