"""Validated switching point for mock, deterministic Tavily, and agent modes."""

from __future__ import annotations

from typing import AsyncIterator

from .schema import FacetResult, ProvisionalVerdict
from .settings import get_settings


async def run_pipeline(topic: str) -> AsyncIterator[ProvisionalVerdict | FacetResult]:
    mode = get_settings().pipeline_mode
    if mode == "mock":
        from .mock_pipeline import run
    elif mode == "tavily":
        from .tavily_pipeline import run
    else:
        # Keeps the optional Anthropic dependency and client construction off mock/Tavily paths.
        from .agent_pipeline import run

    async for item in run(topic):
        yield item
