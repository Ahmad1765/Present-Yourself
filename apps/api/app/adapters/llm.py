"""LLM adapter — same interface across OpenAI, Anthropic, Gemini.

The author_blueprint method takes a research brief + generation settings + (optional)
design tokens, and returns a validated SlideBlueprint.
"""

from __future__ import annotations

import json
from typing import Protocol

import structlog
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.slide import SlideBlueprint

log = structlog.get_logger()


SYSTEM_PROMPT = """You are a presentation designer. Given a research brief and settings,
produce a slide deck as JSON that conforms exactly to the SlideBlueprint schema.

Rules:
- Exactly the number of slides requested.
- Include narrative variety: do not repeat slide types more than twice in a row.
- The first slide MUST be type "title".
- The last slide MUST be type "closing".
- Each slide has speaker notes >= 40 words.
- For image_caption slides, set element.kind="image" with role=null and leave source.url empty
  (the system will fetch images afterwards using `alt` as the search query).
- All citation IDs referenced in slides must exist in deck.citations.
- Output ONLY the JSON, no prose, no markdown fences.
"""


class LLMAdapter(Protocol):
    name: str

    async def author_blueprint(
        self,
        *,
        topic: str,
        brief: str | None,
        research: list[dict],
        slide_count: int,
        language: str,
        tone: str | None,
        audience: str | None,
        design_tokens: dict | None,
    ) -> SlideBlueprint: ...


def _build_user_prompt(
    *,
    topic: str,
    brief: str | None,
    research: list[dict],
    slide_count: int,
    language: str,
    tone: str | None,
    audience: str | None,
    design_tokens: dict | None,
) -> str:
    return json.dumps(
        {
            "topic": topic,
            "brief": brief,
            "slide_count": slide_count,
            "language": language,
            "tone": tone,
            "audience": audience,
            "design_tokens": design_tokens,
            "research": research,
            "schema_hint": (
                "SlideBlueprint v1.0. Top-level keys: schema_version='1.0', deck. "
                "deck has: id, title, language, design_tokens, slides[], citations[]."
            ),
        },
        ensure_ascii=False,
    )


def _validate_or_raise(text: str) -> SlideBlueprint:
    try:
        data = json.loads(text)
        return SlideBlueprint.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"LLM produced invalid SlideBlueprint: {e}") from e


class OpenAIAdapter:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-2024-11-20") -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def author_blueprint(self, **kw) -> SlideBlueprint:
        user_prompt = _build_user_prompt(**kw)
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.6,
        )
        text = resp.choices[0].message.content or "{}"
        return _validate_or_raise(text)


class AnthropicAdapter:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-opus-4-7") -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def author_blueprint(self, **kw) -> SlideBlueprint:
        user_prompt = _build_user_prompt(**kw)
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in msg.content if block.type == "text")
        return _validate_or_raise(text)


class GeminiAdapter:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp") -> None:
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def author_blueprint(self, **kw) -> SlideBlueprint:
        user_prompt = _build_user_prompt(**kw)
        resp = await self.client.aio.models.generate_content(
            model=self.model,
            contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
            config={"response_mime_type": "application/json"},
        )
        return _validate_or_raise(resp.text or "{}")


_REGISTRY: dict[str, type] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "gemini": GeminiAdapter,
}


def get_llm_adapter(provider: str, api_key: str) -> LLMAdapter:
    cls = _REGISTRY.get(provider)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {provider}")
    return cls(api_key=api_key)  # type: ignore[no-any-return]
