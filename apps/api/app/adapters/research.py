"""Research adapter — Tavily primary, extensible. Returns normalized brief items."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, TypedDict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class BriefItem(TypedDict):
    id: str
    url: str
    title: str
    publisher: str | None
    snippet: str
    fetched_at: str


class ResearchAdapter(Protocol):
    name: str

    async def search(self, query: str, *, max_results: int = 8) -> list[BriefItem]: ...


class TavilyAdapter:
    name = "tavily"
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
    async def search(self, query: str, *, max_results: int = 8) -> list[BriefItem]:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                self.endpoint,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            r.raise_for_status()
            data = r.json()
        ts = datetime.now(timezone.utc).isoformat()
        items: list[BriefItem] = []
        for i, res in enumerate(data.get("results", [])):
            items.append(
                BriefItem(
                    id=f"src_{i+1}",
                    url=res.get("url", ""),
                    title=res.get("title", ""),
                    publisher=res.get("source"),
                    snippet=(res.get("content") or "")[:1200],
                    fetched_at=ts,
                )
            )
        return items


def get_research_adapter(provider: str, api_key: str) -> ResearchAdapter:
    if provider == "tavily":
        return TavilyAdapter(api_key=api_key)
    raise ValueError(f"Unknown research provider: {provider}")
