"""
pro_agent.py — Finds supporting evidence.

Simpler than Con-Agent. If Pro doesn't work, Con definitely won't.
Build Con first (per the design doc's advice), then mirror the
structure here for Pro.

Public API:
    run_pro(facet_query: FacetQuery) -> ProResult
"""
from __future__ import annotations

from grounding import SearchResult, fetch, search
from llm import call_json
from prompts import PRO_SYSTEM, build_user_message
from schemas import Claim, FacetQuery, ProResult


def _gather_evidence(queries: list[str]) -> tuple[list[dict], list[str]]:
    """
    Run the search queries, dedupe URLs, fetch pages, return
    evidence list ready for the prompt + list of source URLs.
    """
    seen: set[str] = set()
    evidence: list[dict] = []

    for q in queries:
        for r in search(q):
            if r.url in seen:
                continue
            seen.add(r.url)
            page_text = fetch(r.url)
            evidence.append({
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet,
                "page_text": page_text,
                "published_date": r.published_date,
            })
            if len(evidence) >= 8:  # cap per facet to control prompt size
                break
        if len(evidence) >= 8:
            break

    return evidence, list(seen)


def run_pro(facet_query: FacetQuery) -> tuple[ProResult, list[str]]:
    """
    Run the Pro agent for one facet.

    Returns (ProResult, urls_examined) so the Judge can later verify that
    cited URLs actually appeared in our search results (provenance check).
    """
    evidence, urls_examined = _gather_evidence(facet_query.queries)

    if not evidence:
        # No search results at all — honest empty output
        return ProResult(claims=[]), urls_examined

    user_msg = build_user_message(
        topic=facet_query.topic,
        facet_name=facet_query.facet_name,
        evidence=evidence,
    )

    try:
        raw = call_json(system=PRO_SYSTEM, user=user_msg)
    except ValueError as e:
        print(f"[pro_agent] LLM JSON failure: {e}")
        return ProResult(claims=[]), urls_examined

    # Coerce into schema; drop malformed claims silently
    claims: list[Claim] = []
    for c in raw.get("claims", []) or []:
        try:
            claims.append(Claim(**c))
        except Exception as e:  # noqa: BLE001
            print(f"[pro_agent] skipping malformed claim: {e}")
            continue

    return ProResult(claims=claims), urls_examined
