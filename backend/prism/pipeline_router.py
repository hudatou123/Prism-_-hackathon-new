"""
Pipeline Router — Single switching point between mock and real pipeline.
Controlled by env var PRISM_PIPELINE_MODE = "mock" | "real" (default "mock").
"""

import os
from typing import AsyncIterator, Union
from .schema import ProvisionalVerdict, FacetResult
from . import mock_pipeline, real_pipeline

PIPELINE_MODE = os.getenv("PRISM_PIPELINE_MODE", "mock")


async def run_pipeline(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Yields items in this order (streaming, not batch):
      1. Exactly one ProvisionalVerdict (within ~3 seconds)
      2. One FacetResult per facet (3 total for MVP), as each resolves

    Final verdict is NOT yielded here — the main.py SSE endpoint computes it
    after the async iterator exhausts.
    """
    if PIPELINE_MODE == "real":
        async for item in real_pipeline.run(topic):
            yield item
    else:
        # Default to mock
        async for item in mock_pipeline.run(topic):
            yield item
