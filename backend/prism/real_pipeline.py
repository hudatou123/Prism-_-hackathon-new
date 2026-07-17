"""
Real Pipeline — Placeholder for Person A's RocketRide integration.
Stub interface now so mock-real swap is one env var later.
"""

from typing import AsyncIterator, Union
from .schema import ProvisionalVerdict, FacetResult


async def run(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Real pipeline integration stub. Same signature as mock_pipeline.run.

    TODO: Awaiting Person A's RocketRide pipeline endpoints
    Need from Person A:
    - Fast-path endpoint URL (returns ProvisionalVerdict)
    - Per-facet endpoint URLs (or single endpoint with facet_id param)
    - Auth mechanism (API key? Bearer token?)
    - Response format validation (should match FacetResult schema; add adapter here if not)
    - Error handling strategy
    - Timeout configuration
    - Retry policy
    """
    raise NotImplementedError("Awaiting Person A's RocketRide pipeline endpoints")
    yield  # Make this a generator (unreachable but satisfies type checker)
