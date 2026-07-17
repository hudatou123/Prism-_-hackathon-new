"""
Real Pipeline — Adapter for Person A's RocketRide pipeline.
Transforms Person A's schema to Person D's schema and wraps sync calls in async generator.
"""

import asyncio
import logging
from typing import AsyncIterator, Union
from urllib.parse import urlparse
from .schema import ProvisionalVerdict, FacetResult, Argument

logger = logging.getLogger(__name__)

# Import Person A's pipeline (adjust sys.path to find pipeline/ modules)
import sys
from pathlib import Path

# Person A's pipeline uses local imports (e.g., "from con_agent import..."),
# so we need to add the pipeline/ directory itself to sys.path
repo_root = Path(__file__).parent.parent.parent
pipeline_dir = repo_root / "pipeline"

if str(pipeline_dir) not in sys.path:
    sys.path.insert(0, str(pipeline_dir))

# Now import Person A's modules (they'll find each other via local imports)
try:
    from schemas import FacetQuery, FacetResult as PersonAFacetResult, VerifiedClaim
    from facet_runner import run_facet
except ImportError as e:
    # Fallback error message if pipeline module not found
    import logging
    logging.error(f"Failed to import Person A's pipeline: {e}")
    logging.error(f"Pipeline directory: {pipeline_dir}")
    logging.error(f"Pipeline directory exists: {pipeline_dir.exists()}")
    raise


async def run(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Real pipeline — delegates to Person A's facet_runner with schema adaptation.

    Person A's schema differs from Person D's spec:
    - facet_name (str) → facet_id (Literal)
    - verdict (FacetVerdict) → status (FacetStatus)
    - pro_claims/con_claims (VerifiedClaim) → pro_arguments/con_arguments (Argument)
    - Missing: summary field

    This adapter bridges the gap.
    """
    # 1. Yield provisional verdict first (Person A didn't ship fast path, so generate placeholder)
    await asyncio.sleep(0.5)  # Simulate fast-path delay
    yield ProvisionalVerdict(
        verdict="Analyzing...",
        reasoning="Running detailed fact-checking across multiple facets",
        sources_so_far=0
    )

    # 2. Run each facet (Person A's runner is synchronous, wrap in asyncio)
    facet_ids = ["fact", "scale", "stakeholder_reactions"]

    for facet_id in facet_ids:
        try:
            # Build Person A's input
            facet_query = FacetQuery(
                facet_name=facet_id,
                topic=topic,
                queries=[topic],  # Simple query list — Person A's decomposer would expand this
                is_settled_fact=False
            )

            # Run in thread pool (Person A's code is CPU-bound with LLM calls)
            person_a_result: PersonAFacetResult = await asyncio.to_thread(run_facet, facet_query)

            # Transform to Person D's schema
            person_d_result = _adapt_facet_result(person_a_result, topic)

            yield person_d_result

        except Exception as e:
            # Per-facet failure isolation: log error and yield fallback result
            logger.error(
                f"Facet '{facet_id}' failed for topic '{topic}': {type(e).__name__}: {e}",
                exc_info=True
            )

            # Yield fallback FacetResult so stream continues
            yield FacetResult(
                facet_id=facet_id,
                status="unclear",
                summary="Analysis unavailable for this facet — see logs",
                pro_arguments=[],
                con_arguments=[],
                sources_examined=0,
                quotes_verified=0
            )


def _adapt_facet_result(a_result: PersonAFacetResult, topic: str) -> FacetResult:
    """
    Transform Person A's FacetResult to Person D's FacetResult schema.
    """
    # Map verdict → status (same values, different names)
    status_map = {
        "confirmed": "confirmed",
        "mostly_confirmed": "mostly_confirmed",
        "disputed": "disputed",
        "refuted": "refuted",
        "unclear": "unclear"
    }

    # Generate summary (Person A didn't include this field)
    if a_result.con_abstained:
        summary = f"No credible counter-evidence found for {a_result.facet_name}"
    else:
        summary = f"{a_result.facet_name.replace('_', ' ').title()} analysis: {a_result.verdict}"

    # Transform claims
    pro_arguments = [_adapt_verified_claim(vc, "pro") for vc in a_result.pro_claims]
    con_arguments = [_adapt_verified_claim(vc, "con") for vc in a_result.con_claims]

    return FacetResult(
        facet_id=a_result.facet_name,
        status=status_map.get(a_result.verdict, "unclear"),
        summary=summary,
        pro_arguments=pro_arguments,
        con_arguments=con_arguments,
        sources_examined=a_result.sources_examined,
        quotes_verified=a_result.quotes_verified
    )


def _adapt_verified_claim(vc: VerifiedClaim, side: str) -> Argument:
    """
    Transform Person A's VerifiedClaim to Person D's Argument schema.
    """
    claim = vc.claim

    # Extract domain from URL
    try:
        domain = urlparse(claim.url).netloc
    except:
        domain = "unknown"

    # Map quality_tier → source_quality (same values)
    quality_map = {
        "high": "high",
        "medium": "medium",
        "low": "low"
    }

    # Determine quote_verified (Person A's VerifiedClaim means quote was verified)
    quote_verified = (vc.match_type in ["exact", "paraphrased"])

    return Argument(
        claim=claim.statement,
        quote=claim.quote,
        url=claim.url,
        source_domain=domain,
        published_date=claim.published_date,
        quote_verified=quote_verified,
        source_quality=quality_map.get(vc.quality_tier, "medium")
    )
