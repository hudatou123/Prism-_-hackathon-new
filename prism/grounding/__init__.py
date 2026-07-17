"""Grounding layer (§5) — a thin provider-agnostic interface.

All agents call search()/fetch() and never know the provider underneath
(CH0's whole point). `get_grounding()` picks the right one:
  - keys present  -> Tavily search + httpx/trafilatura fetch, disk-cached (F7)
  - no keys       -> cached hero-topic fixture, so the demo runs with zero setup
"""
from __future__ import annotations

from ..config import settings
from .interface import Grounding, SearchResult
from .cache import DiskCache


def get_grounding() -> Grounding:
    cache = DiskCache(settings.cache_dir) if settings.cache_enabled else None
    if settings.offline:
        from .mock_provider import MockGrounding
        return MockGrounding(cache=cache)
    from .tavily_provider import TavilyGrounding
    return TavilyGrounding(
        tavily_api_key=settings.tavily_api_key,
        user_agent=settings.reddit_user_agent,
        cache=cache,
    )


__all__ = ["Grounding", "SearchResult", "get_grounding", "DiskCache"]
