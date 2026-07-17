"""Lazy Anthropic adapter layered over the secure deterministic evidence pipeline."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from .schema import FacetResult, ProvisionalVerdict
from .settings import get_settings
from .tavily_pipeline import FACET_QUERY_SETS, _run_facet


class LazyAgentAdapter:
    """Import and construct the optional SDK only when agent mode actually runs."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=get_settings().anthropic_api_key)
        return self._client

    def early_read(self, topic: str) -> str:
        response = self._get_client().messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=100,
            temperature=0,
            system=(
                "Give one cautious sentence describing what must be checked in this claim. "
                "Do not assert facts or cite sources; evidence gathering has not happened yet."
            ),
            messages=[{"role": "user", "content": topic}],
        )
        text_blocks = [getattr(block, "text", "") for block in response.content]
        return " ".join(text for text in text_blocks if text).strip() or "Gathering evidence."


_adapter = LazyAgentAdapter()


async def run(topic: str) -> AsyncIterator[ProvisionalVerdict | FacetResult]:
    early_read = await asyncio.to_thread(_adapter.early_read, topic)
    yield ProvisionalVerdict(verdict=early_read, reasoning=early_read, sources_so_far=0)
    tasks = [asyncio.create_task(_run_facet(topic, facet_id)) for facet_id in FACET_QUERY_SETS]
    try:
        for completed in asyncio.as_completed(tasks):
            yield await completed
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
