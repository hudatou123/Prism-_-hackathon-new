"""Deterministic Tavily-only pipeline with exact fetched-page evidence."""

from __future__ import annotations

import asyncio
import re
from typing import AsyncIterator, Literal
from urllib.parse import urlsplit

from .grounding import SearchResult, fetch, search
from .quote_verify import verify_quote
from .schema import Argument, FacetId, FacetResult, ProvisionalVerdict

Side = Literal["pro", "con"]
FACET_QUERY_SETS: dict[FacetId, tuple[tuple[Side, str], ...]] = {
    "fact": (
        ("pro", '"{claim}" evidence primary source'),
        ("con", '"{claim}" false misleading fact check'),
        ("pro", '"{claim}" independent reporting'),
    ),
    "scale": (
        ("pro", '"{claim}" numbers amount percentage scope'),
        ("con", '"{claim}" disputed estimate different figures'),
        ("pro", '"{claim}" official data statistics'),
    ),
    "stakeholder_reactions": (
        ("pro", '"{claim}" official stakeholder reaction statement'),
        ("con", '"{claim}" criticism opposition reaction'),
        ("pro", '"{claim}" public employee community response'),
    ),
}


def _domain(url: str) -> str:
    return (urlsplit(url).hostname or "unknown").removeprefix("www.")


def _quality(domain: str) -> Literal["high", "medium", "low"]:
    if domain.endswith((".gov", ".edu", ".int")):
        return "high"
    if domain in {"reuters.com", "apnews.com", "bbc.com", "nasa.gov"}:
        return "high"
    return "medium"


def _quote_from_page(page: str, hint: str) -> str:
    """Select a literal page substring; never generate or paraphrase a quote."""
    candidates = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", page) if len(part.strip()) >= 35]
    if not candidates:
        return page.strip()[:320]
    hint_words = set(re.findall(r"[a-z0-9]+", hint.lower()))
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (-len(hint_words & set(re.findall(r"[a-z0-9]+", item[1].lower()))), item[0]),
    )
    return ranked[0][1][:500]


def _stakeholder_kind(query_index: int) -> Literal["named", "grassroots"]:
    return "grassroots" if query_index == 2 else "named"

async def _run_searches(topic: str, facet_id: FacetId) -> list[tuple[Side, int, SearchResult]]:
    query_specs = FACET_QUERY_SETS[facet_id]
    calls = [asyncio.to_thread(search, template.format(claim=topic), 4) for _, template in query_specs]
    batches = await asyncio.gather(*calls)
    combined: list[tuple[Side, int, SearchResult]] = []
    seen: set[tuple[Side, str]] = set()
    for index, ((side, _), results) in enumerate(zip(query_specs, batches)):
        for result in results:
            key = (side, result.url)
            if key not in seen:
                seen.add(key)
                combined.append((side, index, result))
    return combined


async def _run_facet(topic: str, facet_id: FacetId) -> FacetResult:
    results = await _run_searches(topic, facet_id)
    pages = await asyncio.gather(*(asyncio.to_thread(fetch, result.url) for _, _, result in results))
    pro: list[Argument] = []
    con: list[Argument] = []
    quotes_attempted = 0
    quotes_verified = 0
    con_searched = sum(1 for side, _, _ in results if side == "con")

    for (side, query_index, result), page in zip(results, pages):
        if not page:
            continue
        quote = _quote_from_page(page, result.snippet or result.title)
        if not quote:
            continue
        quotes_attempted += 1
        verified = verify_quote(quote, page)
        if not verified:
            continue
        quotes_verified += 1
        domain = _domain(result.url)
        argument = Argument(
            claim=result.title or quote[:120],
            quote=quote,
            url=result.url,
            source_domain=domain,
            published_date=result.published_date,
            quote_verified=True,
            source_quality=_quality(domain),
            stakeholder_kind=_stakeholder_kind(query_index) if facet_id == "stakeholder_reactions" else None,
        )
        (pro if side == "pro" else con).append(argument)

    if pro and con:
        status = "disputed"
        summary = "Verified sources present both supporting and counter evidence."
    elif pro and con_searched:
        status = "mostly_confirmed"
        summary = f"Supporting evidence verified; no verified counter evidence in {con_searched} counter results."
    elif con and not pro:
        status = "refuted"
        summary = "Verified counter evidence was found, with no verified supporting evidence."
    else:
        status = "unclear"
        summary = "Insufficient exact, fetched-page evidence to assess this facet."

    return FacetResult(
        facet_id=facet_id,
        status=status,
        summary=summary,
        pro_arguments=pro,
        con_arguments=con,
        sources_examined=len(results),
        quotes_attempted=quotes_attempted,
        quotes_verified=quotes_verified,
        con_empty=bool(con_searched and not con),
        con_searched=con_searched,
    )

async def run(topic: str) -> AsyncIterator[ProvisionalVerdict | FacetResult]:
    """Run all three fixed facet query sets concurrently and stream completions."""
    yield ProvisionalVerdict(
        verdict="Gathering evidence",
        reasoning="No evidence has been counted until search results are fetched and checked.",
        sources_so_far=0,
    )
    tasks = [asyncio.create_task(_run_facet(topic, facet_id)) for facet_id in FACET_QUERY_SETS]
    try:
        for completed in asyncio.as_completed(tasks):
            yield await completed
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
