"""
Verdict Synthesizer — aggregates per-facet results into a final verdict with transparent confidence.
"""

from .schema import FacetResult, FinalVerdict, ConfidenceInputs, ConfidenceBand, FacetId


# Score mapping (F6, corrected version)
STATUS_SCORES = {
    "confirmed": 1.0,
    "mostly_confirmed": 0.75,
    "disputed": 0.5,
    "refuted": 0.0,
    "unclear": None  # Excluded from average
}


def synthesize(facets: list[FacetResult]) -> FinalVerdict:
    """
    Take 3 FacetResults → produce FinalVerdict with transparent confidence.
    """
    if not facets:
        raise ValueError("Cannot synthesize verdict from empty facet list")

    # Compute facet scores
    facet_scores: dict[FacetId, float | None] = {}
    scored_facets = []

    for facet in facets:
        score = STATUS_SCORES.get(facet.status)
        facet_scores[facet.facet_id] = score
        if score is not None:  # Exclude 'unclear' from average
            scored_facets.append((facet.facet_id, score, facet.status))

    # Average score (None if all facets unclear)
    if scored_facets:
        average_score = sum(s for _, s, _ in scored_facets) / len(scored_facets)
    else:
        average_score = None

    # Count sources
    sources_examined_total = sum(f.sources_examined for f in facets)
    quotes_verified_total = sum(f.quotes_verified for f in facets)

    # Sources agreeing (Pro arguments where source_quality != "low" and facet status is not refuted)
    sources_agreeing = 0
    sources_total = 0

    for facet in facets:
        if facet.status != "refuted":
            sources_agreeing += sum(
                1 for arg in facet.pro_arguments if arg.source_quality != "low"
            )
        sources_total += len([arg for arg in facet.pro_arguments if arg.source_quality != "low"])
        sources_total += len([arg for arg in facet.con_arguments if arg.source_quality != "low"])

    # Build confidence inputs
    confidence_inputs = ConfidenceInputs(
        facet_scores=facet_scores,
        scored_facets_count=len(scored_facets),
        average_score=average_score,
        sources_agreeing=sources_agreeing,
        sources_total=sources_total
    )

    # Compute confidence band
    confidence_band = compute_confidence_band(confidence_inputs, facets)

    # Generate verdict headline
    verdict = generate_verdict_headline(facets)

    return FinalVerdict(
        verdict=verdict,
        confidence_band=confidence_band,
        confidence_inputs=confidence_inputs,
        sources_examined_total=sources_examined_total,
        quotes_verified_total=quotes_verified_total
    )


def compute_confidence_band(inputs: ConfidenceInputs, facets: list[FacetResult]) -> ConfidenceBand:
    """
    Compute confidence band based on transparent rules.
    """
    # All facets unclear → CONTESTED
    if inputs.average_score is None:
        return "CONTESTED"

    # Count refuted and confirmed facets
    refuted_count = sum(1 for f in facets if f.status == "refuted")
    confirmed_count = sum(1 for f in facets if f.status == "confirmed")

    # ≥50% refuted OR mix of refuted + confirmed → CONTESTED
    if refuted_count >= len(facets) * 0.5:
        return "CONTESTED"
    if refuted_count > 0 and confirmed_count > 0:
        return "CONTESTED"

    # Based on average score
    avg = inputs.average_score
    if avg >= 0.85:
        return "HIGH"
    elif avg >= 0.60:
        return "MODERATE"
    else:
        return "LOW"


def generate_verdict_headline(facets: list[FacetResult]) -> str:
    """
    Rule-based verdict headline generation (not LLM).
    """
    statuses = [f.status for f in facets]
    status_set = set(statuses)

    # All unclear
    if status_set == {"unclear"}:
        return "INSUFFICIENT EVIDENCE"

    # Any refuted
    refuted_facets = [f.facet_id for f in facets if f.status == "refuted"]
    if refuted_facets:
        return f"REFUTED on {', '.join(refuted_facets)}"

    # All confirmed
    if status_set == {"confirmed"}:
        return "CONFIRMED"

    # All disputed
    if status_set == {"disputed"}:
        return "DISPUTED across all facets"

    # Mix of confirmed + disputed
    disputed_facets = [f.facet_id for f in facets if f.status == "disputed"]
    if "confirmed" in status_set and "disputed" in status_set:
        disputed_names = ', '.join(disputed_facets)
        return f"MOSTLY TRUE — {disputed_names} disputed"

    # Mix of mostly_confirmed + others
    if "mostly_confirmed" in status_set:
        uncertain_facets = [f.facet_id for f in facets if f.status in ["disputed", "unclear"]]
        if uncertain_facets:
            return f"MOSTLY TRUE — {', '.join(uncertain_facets)} uncertain"
        return "MOSTLY TRUE"

    # Default fallback
    return "MIXED EVIDENCE"
