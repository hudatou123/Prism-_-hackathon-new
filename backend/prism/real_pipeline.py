"""
Real Pipeline — Placeholder for Person A's RocketRide integration.
Stub interface now so mock-real swap is one env var later.
"""

from typing import AsyncIterator, Union
from .schema import ProvisionalVerdict, FacetResult


async def run(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Real pipeline integration — awaiting Person A's RocketRide endpoints.

    TODO: Person A must provide:
    - Fast-path endpoint URL (returns ProvisionalVerdict-compatible response)
    - Per-facet endpoint URLs (returns FacetResult-compatible responses)
    - Auth mechanism (API key? Bearer token?)
    - Response format (add adapter here if not matching FacetResult schema)
    - Timeout + retry policy

    Once endpoints exist, replace this body with:
      1. Fire fast-path call → yield ProvisionalVerdict
      2. Fire 3 parallel facet calls (Fact, Scale, Stakeholder Reactions)
      3. As each resolves, yield FacetResult
    Use httpx.AsyncClient for HTTP; wrap in try/except so a single facet failure
    doesn't abort the whole stream.
    """
    raise NotImplementedError(
        "real_pipeline.run() awaiting Person A's RocketRide endpoints. "
        "See TODO comment above. Set PRISM_PIPELINE_MODE=mock to use mock data."
    )
    # The unreachable yield below is required so Python treats this as an async generator.
    if False:
        yield  # type: ignore[unreachable]
