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
    },
    "byd tesla": {
        "provisional": ProvisionalVerdict(
            verdict="True with context required",
            reasoning="BYD overtook Tesla in global EV sales during specific quarters in 2023-2024, though annual totals vary by methodology",
            sources_so_far=5
        ),
        "facets": [
            FacetResult(
                facet_id="fact",
                status="confirmed",
                summary="BYD surpassed Tesla in quarterly sales in late 2023",
                pro_arguments=[
                    Argument(
                        claim="BYD sold more EVs than Tesla in Q4 2023",
                        quote="BYD Auto is a Chinese automobile manufacturer headquartered in Xi'an, Shaanxi, China. It is a subsidiary of BYD Company, a publicly listed Chinese multinational manufacturing conglomerate.",
                        url="https://en.wikipedia.org/wiki/BYD_Auto",
                        source_domain="wikipedia.org",
                        published_date="2024-01-02",
                        quote_verified=True,
                        source_quality="high"
                    ),
                    Argument(
                        claim="Multiple quarters showed BYD leading in battery-electric vehicles",
                        quote="BYD has become one of the world's largest manufacturers of battery electric vehicles and plug-in hybrid vehicles.",
                        url="https://en.wikipedia.org/wiki/BYD_Auto",
                        source_domain="wikipedia.org",
                        published_date="2024-01-02",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[],
                sources_examined=10,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="scale",
                status="mostly_confirmed",
                summary="BYD leads in plug-in hybrids and battery-electric combined, Tesla leads in pure BEV",
                pro_arguments=[
                    Argument(
                        claim="BYD's total includes both BEVs and PHEVs, broader category than Tesla",
                        quote="BYD manufactures both battery electric vehicles and plug-in hybrid electric vehicles.",
                        url="https://en.wikipedia.org/wiki/BYD_Auto",
                        source_domain="wikipedia.org",
                        published_date="2024-01-02",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[
                    Argument(
                        claim="When counting only battery-electric, Tesla maintained lead in some periods",
                        quote="Tesla is a major manufacturer of battery electric vehicles with global distribution.",
                        url="https://en.wikipedia.org/wiki/Tesla,_Inc.",
                        source_domain="wikipedia.org",
                        published_date="2024-01-02",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                sources_examined=14,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="stakeholder_reactions",
                status="mostly_confirmed",
                summary="Industry analysts acknowledged shift, Tesla emphasized different metrics",
                pro_arguments=[
                    Argument(
                        claim="Elon Musk acknowledged competition from Chinese EV makers",
                        quote="Musk has publicly acknowledged the competitiveness of Chinese electric vehicle manufacturers.",
                        url="https://en.wikipedia.org/wiki/Elon_Musk",
                        source_domain="wikipedia.org",
                        published_date="2024-01-15",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="named",
                        stakeholder_name="CEO Elon Musk"
                    )
                ],
                con_arguments=[],
                sources_examined=8,
                quotes_verified=1
            )
        ]
    },
    "bitcoin etf": {
        "provisional": ProvisionalVerdict(
            verdict="Confirmed — multiple approvals in January 2024",
            reasoning="SEC approved 11 spot Bitcoin ETF applications on January 10, 2024, marking historic shift in crypto regulation",
            sources_so_far=6
        ),
        "facets": [
            FacetResult(
                facet_id="fact",
                status="confirmed",
                summary="SEC approved spot Bitcoin ETFs in January 2024",
                pro_arguments=[
                    Argument(
                        claim="SEC granted approval to 11 spot Bitcoin ETFs on January 10, 2024",
                        quote="A spot bitcoin exchange-traded fund is an exchange-traded fund that tracks the market price of bitcoin. The SEC approved 11 bitcoin ETFs in January 2024.",
                        url="https://en.wikipedia.org/wiki/Spot_bitcoin_exchange-traded_fund",
                        source_domain="wikipedia.org",
                        published_date="2024-01-10",
                        quote_verified=True,
                        source_quality="high"
                    ),
                    Argument(
                        claim="Major financial institutions launched products same month",
                        quote="Spot Bitcoin ETFs began trading on major U.S. exchanges in January 2024.",
                        url="https://en.wikipedia.org/wiki/Spot_bitcoin_exchange-traded_fund",
                        source_domain="wikipedia.org",
                        published_date="2024-01-11",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[],
                sources_examined=9,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="scale",
                status="confirmed",
                summary="Approval included BlackRock, Fidelity, and 9 other major issuers",
                pro_arguments=[
                    Argument(
                        claim="BlackRock and Fidelity were among approved issuers",
                        quote="The approved issuers included some of the largest asset management firms globally.",
                        url="https://en.wikipedia.org/wiki/Spot_bitcoin_exchange-traded_fund",
                        source_domain="wikipedia.org",
                        published_date="2024-01-10",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[],
                sources_examined=7,
                quotes_verified=1
            ),
            FacetResult(
                facet_id="stakeholder_reactions",
                status="disputed",
                summary="Mixed reactions: crypto advocates celebrated, skeptics raised concerns",
                pro_arguments=[
                    Argument(
                        claim="SEC Chair Gary Gensler emphasized investor protection framework",
                        quote="The SEC's approval was accompanied by statements emphasizing regulatory oversight.",
                        url="https://en.wikipedia.org/wiki/Gary_Gensler",
                        source_domain="wikipedia.org",
                        published_date="2024-01-10",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="named",
                        stakeholder_name="SEC Chair Gary Gensler"
                    )
                ],
                con_arguments=[
                    Argument(
                        claim="Some critics argued ETF structure contradicts crypto decentralization ethos",
                        quote="Traditional financial intermediaries managing Bitcoin ETFs raised concerns among decentralization advocates.",
                        url="https://en.wikipedia.org/wiki/Bitcoin",
                        source_domain="wikipedia.org",
                        published_date="2024-01-12",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                sources_examined=11,
                quotes_verified=2
            )
        ]
    },
    "twitter advertisers": {
        "provisional": ProvisionalVerdict(
            verdict="Substantially true with ongoing evolution",
            reasoning="Major advertisers paused spending after ownership change in late 2022; some returned gradually through 2023-2024",
            sources_so_far=5
        ),
        "facets": [
            FacetResult(
                facet_id="fact",
                status="confirmed",
                summary="Multiple major advertisers paused campaigns following Twitter/X ownership change",
                pro_arguments=[
                    Argument(
                        claim="Major brands including Apple, Disney, IBM paused advertising in late 2023",
                        quote="Twitter, now known as X, experienced significant advertiser departures following Elon Musk's acquisition.",
                        url="https://en.wikipedia.org/wiki/Twitter",
                        source_domain="wikipedia.org",
                        published_date="2023-11-20",
                        quote_verified=True,
                        source_quality="high"
                    ),
                    Argument(
                        claim="Advertising revenue declined significantly in 2023",
                        quote="X Corp. reported substantial decreases in advertising revenue following the ownership transition.",
                        url="https://en.wikipedia.org/wiki/X_Corp.",
                        source_domain="wikipedia.org",
                        published_date="2023-12-15",
                        quote_verified=True,
                        source_quality="high"
                    )
                ],
                con_arguments=[],
                sources_examined=10,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="scale",
                status="unclear",
                summary="Exact percentage and recovery timeline contested; private company status limits transparency",
                pro_arguments=[
                    Argument(
                        claim="Reports suggested 50-70% revenue decline in early months",
                        quote="Various reports indicated significant advertising revenue decreases, though exact figures varied.",
                        url="https://en.wikipedia.org/wiki/Twitter",
                        source_domain="wikipedia.org",
                        published_date="2023-03-15",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                con_arguments=[
                    Argument(
                        claim="X Corp claimed advertiser return and revenue recovery by mid-2024",
                        quote="Company statements in 2024 suggested improving advertiser relationships.",
                        url="https://en.wikipedia.org/wiki/X_Corp.",
                        source_domain="wikipedia.org",
                        published_date="2024-06-01",
                        quote_verified=True,
                        source_quality="low"
                    )
                ],
                sources_examined=13,
                quotes_verified=2
            ),
            FacetResult(
                facet_id="stakeholder_reactions",
                status="mostly_confirmed",
                summary="Elon Musk publicly confronted advertisers; some cited brand safety concerns",
                pro_arguments=[
                    Argument(
                        claim="Musk made controversial statements about departing advertisers",
                        quote="Elon Musk responded to advertiser departures with public criticism and controversial statements.",
                        url="https://en.wikipedia.org/wiki/Elon_Musk",
                        source_domain="wikipedia.org",
                        published_date="2023-11-30",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="named",
                        stakeholder_name="CEO Elon Musk"
                    ),
                    Argument(
                        claim="Advertisers cited brand safety and content moderation concerns",
                        quote="Major advertisers expressed concerns about content moderation policies and brand safety on the platform.",
                        url="https://en.wikipedia.org/wiki/Twitter",
                        source_domain="wikipedia.org",
                        published_date="2023-11-25",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="grassroots",
                        stakeholder_name="Major brand CMOs"
                    )
                ],
                con_arguments=[],
                sources_examined=9,
                quotes_verified=2
            )
        ]
    },
    "gpt-5": {
        "provisional": ProvisionalVerdict(
            verdict="No public release as of mid-2024",
            reasoning="OpenAI released GPT-4o and other variants in 2024, but no model officially named GPT-5 has been publicly announced",
            sources_so_far=4
        ),
        "facets": [
            FacetResult(
                facet_id="fact",
                status="confirmed",
                summary="No GPT-5 announcement or release from OpenAI as of July 2024",
                pro_arguments=[
                    Argument(
                        claim="OpenAI's latest public releases are GPT-4 variants including GPT-4o",
                        quote="GPT-4 was released in March 2023, with subsequent optimized variants such as GPT-4o following in 2024.",
                        url="https://en.wikipedia.org/wiki/GPT-4",
                        source_domain="wikipedia.org",
                        published_date="2024-05-15",
                        quote_verified=True,
                        source_quality="high"
                    ),
                    Argument(
                        claim="Company statements have not announced GPT-5 development timeline",
                        quote="OpenAI has not publicly announced a GPT-5 model or confirmed its development status.",
                        url="https://en.wikipedia.org/wiki/OpenAI",
                        source_domain="wikipedia.org",
                        published_date="2024-06-01",
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
                status="unclear",
                summary="Speculation exists about future models, but no confirmed specifications",
                pro_arguments=[
                    Argument(
                        claim="Industry speculation about next-generation models continues",
                        quote="The AI industry has speculated about future large language model generations beyond GPT-4.",
                        url="https://en.wikipedia.org/wiki/Large_language_model",
                        source_domain="wikipedia.org",
                        published_date="2024-04-10",
                        quote_verified=True,
                        source_quality="medium"
                    )
                ],
                con_arguments=[],
                sources_examined=6,
                quotes_verified=1
            ),
            FacetResult(
                facet_id="stakeholder_reactions",
                status="mostly_confirmed",
                summary="OpenAI executives have been cautious about discussing future model releases",
                pro_arguments=[
                    Argument(
                        claim="Sam Altman declined to provide GPT-5 timeline in public statements",
                        quote="OpenAI CEO Sam Altman has stated the company is focused on improving existing models rather than rushing to GPT-5.",
                        url="https://en.wikipedia.org/wiki/Sam_Altman",
                        source_domain="wikipedia.org",
                        published_date="2024-03-20",
                        quote_verified=True,
                        source_quality="high",
                        stakeholder_kind="named",
                        stakeholder_name="OpenAI CEO Sam Altman"
                    )
                ],
                con_arguments=[],
                sources_examined=5,
                quotes_verified=1
            )
        ]
    }
}


async def run(topic: str) -> AsyncIterator[Union[ProvisionalVerdict, FacetResult]]:
    """
    Mock pipeline that yields provisional verdict + 3 facets with realistic timing.
    """
    # Match against hero topics (case-insensitive keyword match)
    topic_lower = topic.lower()
    hero_data = None

    # Match on keywords for each hero topic
    if "byd" in topic_lower or "tesla" in topic_lower:
        hero_data = HERO_TOPICS["byd tesla"]
    elif "bitcoin" in topic_lower or "etf" in topic_lower:
        hero_data = HERO_TOPICS["bitcoin etf"]
    elif "twitter" in topic_lower or "advertisers" in topic_lower or "x corp" in topic_lower:
        hero_data = HERO_TOPICS["twitter advertisers"]
    elif "gpt" in topic_lower and "5" in topic_lower:
        hero_data = HERO_TOPICS["gpt-5"]
    elif "meta" in topic_lower or "layoff" in topic_lower:
        hero_data = HERO_TOPICS["meta layoff"]

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
