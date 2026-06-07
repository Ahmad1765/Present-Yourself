"""Extract design tokens from an uploaded PPTX."""

from __future__ import annotations

import io
from typing import Any

from pptx import Presentation
from pptx.util import Emu


def extract_design_tokens(pptx_bytes: bytes) -> dict[str, Any]:
    prs = Presentation(io.BytesIO(pptx_bytes))
    width = int(prs.slide_width or Emu(12192000))
    height = int(prs.slide_height or Emu(6858000))
    aspect = _aspect(width, height)

    palette = _extract_palette(prs)
    fonts = _extract_fonts(prs)

    return {
        "dimensions": {"width_emu": width, "height_emu": height, "aspect": aspect},
        "palette": palette,
        "fonts": fonts,
    }


def _aspect(w: int, h: int) -> str:
    ratio = w / h if h else 0
    if abs(ratio - 16 / 9) < 0.02:
        return "16:9"
    if abs(ratio - 4 / 3) < 0.02:
        return "4:3"
    if abs(ratio - 16 / 10) < 0.02:
        return "16:10"
    return "16:9"


def _extract_palette(prs: Presentation) -> dict[str, str]:
    palette = {
        "background": "#FFFFFF",
        "foreground": "#0F172A",
        "accent1": "#2563EB",
        "accent2": "#0EA5E9",
        "accent3": "#F59E0B",
        "muted": "#64748B",
    }
    if not prs.slide_masters or len(prs.slide_masters) == 0:
        return palette
    try:
        theme_xml = prs.slide_masters[0].element.xpath(
            ".//a:clrScheme",
            namespaces={"a": "http://schemas.openxmlformats.org/drawingml/2006/main"},
        )
        if not theme_xml:
            return palette
        scheme = theme_xml[0]
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        mapping = {
            "dk1": "foreground",
            "lt1": "background",
            "accent1": "accent1",
            "accent2": "accent2",
            "accent3": "accent3",
        }
        for tag, key in mapping.items():
            nodes = scheme.findall(f"a:{tag}", ns)
            if not nodes:
                continue
            srgb = nodes[0].find(".//a:srgbClr", ns)
            if srgb is not None and srgb.get("val"):
                palette[key] = f"#{srgb.get('val').upper()}"
    except Exception:  # noqa: BLE001
        pass
    return palette


def _extract_fonts(prs: Presentation) -> dict[str, dict[str, Any]]:
    heading = "Inter"
    body = "Inter"
    if not prs.slide_masters or len(prs.slide_masters) == 0:
        return {
            "heading": {"family": heading, "weight": 700},
            "body": {"family": body, "weight": 400},
        }
    try:
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        font_scheme = prs.slide_masters[0].element.xpath(".//a:fontScheme", namespaces=ns)
        if font_scheme:
            major = font_scheme[0].find("a:majorFont/a:latin", ns)
            minor = font_scheme[0].find("a:minorFont/a:latin", ns)
            if major is not None and major.get("typeface"):
                heading = major.get("typeface")
            if minor is not None and minor.get("typeface"):
                body = minor.get("typeface")
    except Exception:  # noqa: BLE001
        pass
    return {
        "heading": {"family": heading, "weight": 700},
        "body": {"family": body, "weight": 400},
    }
