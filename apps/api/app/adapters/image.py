"""Image adapters — Unsplash, Pexels, Pixabay. Same interface."""

from __future__ import annotations

from typing import Protocol, TypedDict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ImageResult(TypedDict):
    provider: str
    url: str
    thumb_url: str
    credit: str
    width: int | None
    height: int | None


class ImageAdapter(Protocol):
    name: str

    async def search(self, query: str, *, page: int = 1, per_page: int = 12) -> list[ImageResult]: ...


class UnsplashAdapter:
    name = "unsplash"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def search(self, query: str, *, page: int = 1, per_page: int = 12) -> list[ImageResult]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "page": page, "per_page": per_page, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {self.api_key}"},
            )
            r.raise_for_status()
            data = r.json()
        return [
            ImageResult(
                provider="unsplash",
                url=item["urls"]["regular"],
                thumb_url=item["urls"]["small"],
                credit=f"Photo by {item['user']['name']} on Unsplash",
                width=item.get("width"),
                height=item.get("height"),
            )
            for item in data.get("results", [])
        ]


class PexelsAdapter:
    name = "pexels"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def search(self, query: str, *, page: int = 1, per_page: int = 12) -> list[ImageResult]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "page": page, "per_page": per_page, "orientation": "landscape"},
                headers={"Authorization": self.api_key},
            )
            r.raise_for_status()
            data = r.json()
        return [
            ImageResult(
                provider="pexels",
                url=item["src"]["large"],
                thumb_url=item["src"]["medium"],
                credit=f"Photo by {item['photographer']} on Pexels",
                width=item.get("width"),
                height=item.get("height"),
            )
            for item in data.get("photos", [])
        ]


class PixabayAdapter:
    name = "pixabay"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def search(self, query: str, *, page: int = 1, per_page: int = 12) -> list[ImageResult]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://pixabay.com/api/",
                params={
                    "key": self.api_key,
                    "q": query,
                    "page": page,
                    "per_page": per_page,
                    "image_type": "photo",
                    "orientation": "horizontal",
                },
            )
            r.raise_for_status()
            data = r.json()
        return [
            ImageResult(
                provider="pixabay",
                url=item["largeImageURL"],
                thumb_url=item["webformatURL"],
                credit=f"Image by {item['user']} on Pixabay",
                width=item.get("imageWidth"),
                height=item.get("imageHeight"),
            )
            for item in data.get("hits", [])
        ]


_REGISTRY: dict[str, type] = {
    "unsplash": UnsplashAdapter,
    "pexels": PexelsAdapter,
    "pixabay": PixabayAdapter,
}


def get_image_adapter(provider: str, api_key: str) -> ImageAdapter:
    cls = _REGISTRY.get(provider)
    if cls is None:
        raise ValueError(f"Unknown image provider: {provider}")
    return cls(api_key=api_key)  # type: ignore[no-any-return]
