"""Handoff adapter: Person A's pipeline -> Person D's backend contract.

Person D's FastAPI/SSE backend consumes an async generator that yields, in
order:
  1. exactly one ProvisionalVerdict-shaped item (fast path, ~2-4s)
  2. three FacetResult-shaped items (fact, scale, stakeholder_reactions),
     each as it resolves

This module maps A's INTERNAL schemas (prism.schemas) onto D's EXTERNAL contract
(backend/prism/schema.py). It returns PLAIN DICTS matching D's fields exactly,
because A's package can't import D's Pydantic models (separate repo). D wraps
them on her side: `ProvisionalVerdict(**d)` / `FacetResult(**d)`.

--- How Person D uses this (backend/prism/real_pipeline.py) --------------------

    from prism.integration import run            # drop-in for mock_pipeline.run

    async def run(topic):
        async for item in run(topic):            # item is a dict; wrap if desired
            yield item

Or, for D's "Option B" (fan out fast-path + 3 facets as independent calls):

    from prism.integration import run_fast_path, run_facet, FACET_IDS
    prov = await run_fast_path(topic)
    facets = await asyncio.gather(*(run_facet(fid, topic) for fid in FACET_IDS))

Both paths run today with zero keys (offline fixture) and switch to live
Tavily+Claude when keys are set — no code change.
"""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional
from urllib.parse import urlparse

from .agents.decomposer import decompose
from .agents.fast_path import provisional_verdict
from .agents.procon_judge import FacetAgent, default_facet_agent
from .config import FIXED_FACETS
from .grounding import get_grounding
from .grounding.interface import Grounding
from .orchestrator import run_pipeline
from .schemas import (
    Argument,
    EventType,
    Evidence,
    FacetVerdict,
    ProvisionalVerdict,
)

FACET_IDS: List[str] = [f.key for f in FIXED_FACETS]
_FACET_BY_KEY = {f.key: f for f in FIXED_FACETS}


# --------------------------------------------------------------------------
# Field-level defaults for things A doesn't yet produce natively.
# These are DEFAULTS. Person B replaces source_quality with the real F4
# quality-weighted judgment and fills real stakeholder_name from named sources.
# --------------------------------------------------------------------------

# Static source-quality table (DEFAULT — B refines). Distinct axis from the
# political-lean `source_bias` A already tracks. Domains not listed -> "medium".
_HIGH_QUALITY = {
    "sec.gov", "reuters.com", "apnews.com", "bloomberg.com", "wsj.com",
    "ft.com", "nytimes.com", "washingtonpost.com", "bbc.com", "bbc.co.uk",
    "npr.org", "theguardian.com", "cnbc.com", "economist.com",
}
_LOW_QUALITY_MARKERS = ("reddit.com", "medium.com", "substack.com", ".example.com")


def _domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def _source_quality(url: str) -> str:
    dom = _domain(url)
    if dom in _HIGH_QUALITY:
        return "high"
    if any(marker in url.lower() for marker in _LOW_QUALITY_MARKERS):
        return "low"
    return "medium"


def _stakeholder_fields(ev: Evidence, facet_id: str) -> Dict[str, Optional[str]]:
    """Only populated for the stakeholder_reactions facet (D's schema)."""
    if facet_id != "stakeholder_reactions":
        return {"stakeholder_kind": None, "stakeholder_name": None}
    if ev.author:  # grassroots (Reddit) evidence carries an author handle
        return {"stakeholder_kind": "grassroots", "stakeholder_name": f"u/{ev.author}"}
    # named (news) — B fills the actual person/org name; None is a safe default
    return {"stakeholder_kind": "named", "stakeholder_name": None}


# --------------------------------------------------------------------------
# Shape adapters: A schema -> D dict
# --------------------------------------------------------------------------
def to_provisional_dict(pv: ProvisionalVerdict) -> Dict:
    """A.ProvisionalVerdict -> D.ProvisionalVerdict dict."""
    return {
        "verdict": pv.early_read,
        "reasoning": pv.reasoning or pv.early_read,
        "sources_so_far": pv.sources_so_far,
    }


def _flatten_argument(arg: Argument, facet_id: str) -> List[Dict]:
    """A nests Evidence under Argument; D wants one flat Argument per quote."""
    out: List[Dict] = []
    for ev in arg.evidence:
        out.append(
            {
                "claim": arg.claim,
                "quote": ev.quote,
                "url": ev.url,
                "source_domain": _domain(ev.url),
                "published_date": ev.published_date,
                "quote_verified": ev.quote_verified,
                "source_quality": _source_quality(ev.url),  # DEFAULT (B refines)
                **_stakeholder_fields(ev, facet_id),
            }
        )
    return out


def to_facet_dict(fv: FacetVerdict) -> Dict:
    """A.FacetVerdict -> D.FacetResult dict (evidence flattened)."""
    fid = fv.facet_key
    pro = [a for arg in fv.pro.arguments for a in _flatten_argument(arg, fid)]
    con = [a for arg in fv.con.arguments for a in _flatten_argument(arg, fid)]
    return {
        "facet_id": fid,
        "status": fv.status.value,
        "summary": fv.summary,
        "pro_arguments": pro,
        "con_arguments": con,  # empty list => D renders "no credible counter-evidence"
        "sources_examined": fv.sources_examined,
        "quotes_verified": fv.quotes_verified,
    }


def _unclear_facet_dict(facet_id: str, note: str) -> Dict:
    """A facet that errored -> a valid 'unclear' FacetResult, so D keeps
    streaming the other two instead of aborting the whole request (D's Q6)."""
    return {
        "facet_id": facet_id,
        "status": "unclear",
        "summary": f"Could not resolve this facet: {note}",
        "pro_arguments": [],
        "con_arguments": [],
        "sources_examined": 0,
        "quotes_verified": 0,
    }


# --------------------------------------------------------------------------
# Entry points for Person D
# --------------------------------------------------------------------------
async def run(topic: str) -> AsyncIterator[Dict]:
    """Primary drop-in for D's `mock_pipeline.run` / `real_pipeline.run`.

    Yields D-shaped dicts in resolution order: one provisional, then one per
    facet as each lands. Does NOT yield a final verdict — D's synthesizer
    computes that after the iterator exhausts (per her spec).
    """
    async for ev in run_pipeline(topic):
        if ev.type == EventType.PROVISIONAL and ev.provisional:
            yield {"_kind": "provisional", **to_provisional_dict(ev.provisional)}
        elif ev.type == EventType.FACET_RESOLVED and ev.facet:
            yield {"_kind": "facet", **to_facet_dict(ev.facet)}
        elif ev.type == EventType.ERROR and ev.facet_key:
            # per-facet failure -> unclear facet, keep the stream alive (Q6)
            yield {"_kind": "facet", **_unclear_facet_dict(ev.facet_key, ev.message or "error")}
        # DECOMPOSED / FACET_STARTED / FINAL / DONE are A-internal; D ignores.


async def run_fast_path(topic: str, grounding: Optional[Grounding] = None) -> Dict:
    """Option B helper: just the provisional verdict (D-shaped dict)."""
    own = grounding is None
    grounding = grounding or get_grounding()
    try:
        pv = await provisional_verdict(topic, grounding)
        return to_provisional_dict(pv)
    finally:
        if own:
            await grounding.aclose()


async def run_facet(
    facet_id: str,
    topic: str,
    grounding: Optional[Grounding] = None,
    facet_agent: Optional[FacetAgent] = None,
) -> Dict:
    """Option B helper: resolve ONE facet independently (D-shaped dict).

    Decomposes internally to get this facet's queries. If D fans out all three,
    that's 3 cheap decompose calls; wire a shared decomposition later if it
    matters (it's one fast-model call, and cached under F7).
    """
    if facet_id not in _FACET_BY_KEY:
        raise ValueError(f"unknown facet_id {facet_id!r}; expected one of {FACET_IDS}")
    own = grounding is None
    grounding = grounding or get_grounding()
    facet_agent = facet_agent or default_facet_agent()
    try:
        decomposition = await decompose(topic)
        fq = next((q for q in decomposition.facet_queries if q.facet_key == facet_id), None)
        if fq is None:
            return _unclear_facet_dict(facet_id, "decomposer produced no queries")
        verdict = await facet_agent.run(
            _FACET_BY_KEY[facet_id], fq, grounding, settled=decomposition.settled_fact
        )
        return to_facet_dict(verdict)
    except Exception as exc:  # never abort D's fan-out on one facet (Q6)
        return _unclear_facet_dict(facet_id, f"{type(exc).__name__}: {exc}")
    finally:
        if own:
            await grounding.aclose()
