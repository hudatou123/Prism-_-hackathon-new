"""Verdict Synthesizer + F6 confidence — SEAM owned by Person D.

Person A's orchestrator calls `synthesize(claim, facets)` to produce the FINAL
Level-0 verdict that swaps in over the provisional one (F1). D refines the
prose/weighting; A ships a correct, auditable F6 implementation so the swap and
the confidence card work end-to-end today.

F6 is fully specified, so this is real, not a stub:
  Confirmed=1.0  Mostly=0.75  Disputed=0.5  Refuted=0.0  Unclear=excluded
  confidence = mean of SCORED facets; Unclear lowers coverage, not the score.
Every number shown is derived here from real facet data (F9).
"""
from __future__ import annotations

from typing import List

from .schemas import (
    ConfidenceBand,
    FacetStatus,
    FacetVerdict,
    FinalVerdict,
)


def _band(score: float, contested: bool) -> ConfidenceBand:
    if contested:
        return ConfidenceBand.CONTESTED
    if score >= 0.85:
        return ConfidenceBand.HIGH
    if score >= 0.6:
        return ConfidenceBand.MODERATE
    return ConfidenceBand.LOW


def _verdict_text(facets: List[FacetVerdict], mean: float) -> str:
    fact = next((f for f in facets if f.facet_key == "fact"), None)
    disputed = [f.label for f in facets if f.status == FacetStatus.DISPUTED]
    if fact and fact.status == FacetStatus.REFUTED:
        head = "FALSE"
    elif mean >= 0.85:
        head = "TRUE"
    elif mean >= 0.6:
        head = "MOSTLY TRUE"
    elif mean >= 0.4:
        head = "MIXED"
    else:
        head = "UNSUPPORTED"
    tail = f" — {', '.join(d.lower() for d in disputed)} disputed" if disputed else ""
    return head + tail


def synthesize(claim: str, facets: List[FacetVerdict]) -> FinalVerdict:
    scored = [(f, f.score) for f in facets if f.score is not None]
    mean = sum(s for _, s in scored) / len(scored) if scored else 0.0

    contested = any(f.status == FacetStatus.DISPUTED for f in facets)
    band = _band(mean, contested)

    # Source agreement among verified quotes (F6 shows this ratio with inputs).
    total_quotes = sum(f.quotes_total for f in facets)
    verified_quotes = sum(f.quotes_verified for f in facets)
    agreement = (verified_quotes / total_quotes) if total_quotes else None

    return FinalVerdict(
        claim=claim,
        verdict=_verdict_text(facets, mean),
        confidence_band=band,
        facet_scores={f.facet_key: f.score for f in facets},
        scored_facet_count=len(scored),
        total_facet_count=len(facets),
        source_agreement_ratio=agreement,
        sources_examined=sum(f.sources_examined for f in facets),
        quotes_verified=verified_quotes,
        quotes_total=total_quotes,
    )
