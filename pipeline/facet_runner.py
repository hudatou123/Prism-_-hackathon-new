"""
facet_runner.py — Orchestrates Pro + Con + Judge for one facet.

This is the PUBLIC API of Person B's code. Person A's pipeline calls
    result = run_facet(facet_query)
and gets back a FacetResult ready for Person D's Synthesizer.

The runner also handles the Stakeholder Reactions facet's grassroots
sub-bucket (F5 v2) — for that facet, we run the normal Named-sources
pipeline PLUS merge in Reddit comments as extra Pro claims.
"""
from __future__ import annotations

from con_agent import run_con
from judge import judge_facet
from pro_agent import run_pro
from reddit_fetcher import fetch_grassroots
from schemas import FacetQuery, FacetResult, ProResult


def run_facet(facet_query: FacetQuery) -> FacetResult:
    """
    Run Pro + Con + Judge for one facet. Returns the FacetResult
    that Person D's Synthesizer consumes.

    For 'stakeholder_reactions', additionally merges Reddit grassroots
    comments as extra Pro-side evidence before judging.
    """
    # 1. Pro and Con in sequence (parallelization is Person A's concern
    #    at the pipeline level — we stay simple here)
    pro_result, pro_urls = run_pro(facet_query)
    con_result, con_urls = run_con(facet_query)

    # 2. Stakeholder-Reactions-only: merge grassroots comments
    if facet_query.facet_name == "stakeholder_reactions":
        grassroots_claims, grassroots_urls = fetch_grassroots(facet_query.topic)
        # Treat grassroots as additional Pro-side statements
        # (they're not "opposition" — they're just what people said)
        pro_result = ProResult(claims=pro_result.claims + grassroots_claims)
        pro_urls = pro_urls + grassroots_urls

    # 3. Judge: provenance, quote-grep, quality-weighted verdict
    return judge_facet(
        facet_name=facet_query.facet_name,
        pro=pro_result,
        con=con_result,
        pro_urls_examined=pro_urls,
        con_urls_examined=con_urls,
    )
