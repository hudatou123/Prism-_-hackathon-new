"""
schemas.py — Shared data contracts.

CRITICAL: agree these with Person A (Decomposer output → your input)
and Person D (your FacetResult → Synthesizer input) at hour 0.
If these drift, the whole pipeline stops working.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── What the Decomposer (Person A) hands you ───────────────────────────
class FacetQuery(BaseModel):
    """One facet's worth of search queries, produced by the Decomposer."""
    facet_name: Literal["fact", "scale", "stakeholder_reactions"]
    topic: str  # the original user claim, for context
    queries: list[str] = Field(min_length=1, max_length=3)
    is_settled_fact: bool = False  # if True, skip Con-Agent (F4 short-circuit)


# ── What Pro/Con return ────────────────────────────────────────────────
class Claim(BaseModel):
    """One piece of evidence — a claim, a supporting quote, a URL."""
    statement: str            # the agent's paraphrase of what the source says
    quote: str                # verbatim quote from the page (F3 will grep this)
    url: str                  # must come from search results
    source_title: str = ""
    published_date: Optional[str] = None


class ProResult(BaseModel):
    """Pro-Agent output. Zero claims is valid — means nothing supportive found."""
    claims: list[Claim] = []


class ConResult(BaseModel):
    """
    Con-Agent output. The abstain path (F4) is a first-class value:
    `no_credible_counter_evidence_found=True` with claims=[] is the
    correct output for settled facts, not an error.
    """
    no_credible_counter_evidence_found: bool = False
    reason: str = ""  # only populated when the flag is True
    claims: list[Claim] = []


# ── What the Judge attaches to each claim ──────────────────────────────
class VerifiedClaim(BaseModel):
    """A Claim that has passed provenance + quote-grep."""
    claim: Claim
    quality_tier: Literal["high", "medium", "low"]
    match_type: Literal["exact", "paraphrased"]  # from matching.py


# ── What Person D's Synthesizer consumes ───────────────────────────────
FacetVerdict = Literal[
    "confirmed",        # 1.0
    "mostly_confirmed", # 0.75
    "disputed",         # 0.5
    "refuted",          # 0.0
    "unclear",          # excluded from average — insufficient data
]


class FacetResult(BaseModel):
    """
    Output of running Pro + Con + Judge for one facet.
    This is what Person D's Synthesizer aggregates into the final verdict.
    """
    facet_name: str
    verdict: FacetVerdict
    pro_claims: list[VerifiedClaim] = []
    con_claims: list[VerifiedClaim] = []
    con_abstained: bool = False    # F4: means "no credible opposition"
    abstain_reason: str = ""

    # Real counters for F9 (no decorative numbers)
    sources_examined: int = 0
    quotes_attempted: int = 0
    quotes_verified: int = 0
