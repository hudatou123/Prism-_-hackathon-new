"""Primary grounding: Tavily search() + httpx/trafilatura fetch() (§5).

Fallbacks noted in §5 (Brave, Tavily extract) are left as TODO seams — wire
them if the F7 burst test finds a ceiling.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional

import httpx

from .cache import DiskCache
from .interface import SearchResult

try:
    import trafilatura  # article-text extraction
except ImportError:  # keep import-time failures friendly for teammates
    trafilatura = None


class TavilyGrounding:
    def __init__(
        self,
        tavily_api_key: str,
        user_agent: str = "prism/0.1",
        cache: Optional[DiskCache] = None,
        timeout: float = 15.0,
    ):
        self._key = tavily_api_key
        self._cache = cache
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )

    # -- search() -----------------------------------------------------------
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if self._cache is not None:
            hit = self._cache.get("search", f"{query}|{max_results}")
            if hit is not None:
                return hit

        resp = await self._client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self._key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",  # 1 credit; §5 budget math
            },
        )
        resp.raise_for_status()
        data = resp.json()
        results: List[SearchResult] = [
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "published_date": r.get("published_date"),
            }
            for r in data.get("results", [])
        ]
        if self._cache is not None:
            self._cache.set("search", f"{query}|{max_results}", results)
        return results

    # -- fetch() ------------------------------------------------------------
    async def fetch(self, url: str) -> str:
        if self._cache is not None:
            hit = self._cache.get("fetch", url)
            if hit is not None:
                return hit

        text = ""
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            html = resp.text
            if trafilatura is not None:
                # trafilatura is sync/CPU-bound — keep the event loop free.
                text = await asyncio.to_thread(
                    trafilatura.extract, html, include_comments=False
                ) or ""
            if not text:
                text = html  # last resort: raw HTML still lets grep find a quote
        except (httpx.HTTPError, httpx.TimeoutException):
            text = ""  # a dead fetch means the Judge drops the quote — honest fail

        if self._cache is not None and text:
            self._cache.set("fetch", url, text)
        return text

    async def aclose(self) -> None:
        await self._client.aclose()
