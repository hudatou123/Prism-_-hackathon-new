"""Backward-compatible lazy alias for the supported agent pipeline.

The old module imported an unrelated repository pipeline and described it as a
RocketRide integration. No such integration is provided. New callers should
select ``PRISM_PIPELINE_MODE=agent`` and use :mod:`prism.pipeline_router`.
"""

from __future__ import annotations

from typing import AsyncIterator

from .schema import FacetResult, ProvisionalVerdict


async def run(topic: str) -> AsyncIterator[ProvisionalVerdict | FacetResult]:
    """Delegate lazily so importing this compatibility module loads no agent SDK."""
    from .agent_pipeline import run as run_agent

    async for item in run_agent(topic):
        yield item


__all__ = ["run"]
