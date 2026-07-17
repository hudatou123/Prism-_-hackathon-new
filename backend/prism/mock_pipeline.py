"""
Mock Pipeline — realistic-shaped fake data for parallel frontend development.
Yields ProvisionalVerdict + 3 FacetResults with plausible timing.
"""

import asyncio
from typing import AsyncIterator, Union
from .schema import ProvisionalVerdict, FacetResult, Argument

# Hero topics (matching warm_cache.py)
HERO_TOPICS = {
    "meta layoff": {
        "provisional": ProvisionalVerdict(
            verdict="Likely true, scale disputed",
            reasoning="Multiple credible sources confirm workforce reduction, exact percentage varies",
            sources_so_far=4
        ),
        "facets": [
            FacetResult(
                facet_id="fact",
                status="confirmed",
                summary="Meta announced layoffs affecting approximately 5% of workforce",
                pro_arguments=[
                    Argument(
                        claim="Meta confirmed 5% workforce reduction in March 2023",
                        quote="Meta is laying off about 10,000 employees, or roughly 13% of its workforce.",
                        url="https://en.wikipedia.org/wiki/Meta_Platforms",
                        source_domain="wikipedia.org",
                        published_date="2023-03-14",
                        quote_verified=True,
                        source_quality="high"
                    ),
                    Argument(
                        claim="Official company statement acknowledged restructuring",
                        quote="The company announced plans to restructure and flatten org structure.",
                        url="https://en.wikipedia.org/wiki/Layoff",
                        source_domain="wikipedia.org",
                        published_date="2023-03-14",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[],
                sources_examined=8,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="scale",
                status="disputed",
                summary="Exact percentage varies between 5-13% across different sources",
                pro_arguments=[
                    Argument(
                        claim="Some sources report 13% total across multiple rounds",
                        quote="Meta's total layoffs in 2023 reached approximately 21,000 employees.",
                        url="https://en.wikipedia.org/wiki/Meta_Platforms",
                        source_domain="wikipedia.org",
                        published_date="2023-05-24",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                con_arguments=[
                    Argument(
                        claim="Initial round was closer to 5%, later rounds brought higher total",
                        quote="The first wave of layoffs affected roughly 11,000 employees.",
                        url="https://en.wikipedia.org/wiki/Layoff",
                        source_domain="wikipedia.org",
                        published_date="2023-03-15",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                sources_examined=12,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="stakeholder_reactions",
                status="mostly_confirmed",
                summary="Mixed reactions from employees and analysts",
                pro_arguments=[
                    Argument(
                        claim="CEO cited efficiency and focus as primary drivers",
                        quote="Mark Zuckerberg called 2023 the 'year of efficiency'.",
                        url="https://en.wikipedia.org/wiki/Mark_Zuckerberg",
                        source_domain="wikipedia.org",
                        published_date="2023-03-14",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="named",
                        stakeholder_name="CEO Mark Zuckerberg"
                    )
                ],
                con_arguments=[],
                sources_examined=6,
                quotes_verified=1
            )
        ]
    }
}


async def run(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Mock pipeline that yields provisional verdict + 3 facets with realistic timing.
    """
    # Match against hero topics (case-insensitive substring match)
    topic_lower = topic.lower()
    hero_data = None

    for key, data in HERO_TOPICS.items():
        if key in topic_lower or topic_lower in key:
            hero_data = data
            break

    # Default to generic template if no match
    if hero_data is None:
        hero_data = HERO_TOPICS["meta layoff"]  # Use as template

    # Yield provisional verdict after 2-3s
    await asyncio.sleep(2.5)
    yield hero_data["provisional"]

    # Yield facets with staggered timing (5-8s each)
    for i, facet in enumerate(hero_data["facets"]):
        await asyncio.sleep(5 + i * 1.5)  # 5s, 6.5s, 8s
        yield facet
