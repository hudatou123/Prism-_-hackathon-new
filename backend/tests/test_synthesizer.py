"""
Tests for verdict synthesizer — confidence band logic.
"""

import pytest
from prism.synthesizer import synthesize, compute_confidence_band
from prism.schema import FacetResult, Argument, ConfidenceInputs


def make_facet(facet_id: str, status: str, pro_count: int = 2, con_count: int = 0) -> FacetResult:
    """Helper to create test facets."""
    pro_args = [
        Argument(
            claim=f"Pro {i}",
            quote=f"Quote {i}",
            url=f"https://example.com/{i}",
            source_domain="example.com",
            quote_verified=True,
            source_quality="high"
        ) for i in range(pro_count)
    ]
    con_args = [
        Argument(
            claim=f"Con {i}",
            quote=f"Quote {i}",
            url=f"https://example.com/con{i}",
            source_domain="example.com",
            quote_verified=True,
            source_quality="high"
        ) for i in range(con_count)
    ]
    return FacetResult(
        facet_id=facet_id,
        status=status,
        summary=f"Summary for {facet_id}",
        pro_arguments=pro_args,
        con_arguments=con_args,
        sources_examined=pro_count + con_count + 3,
        quotes_verified=pro_count + con_count
    )


def test_all_confirmed():
    """All confirmed → HIGH, verdict says 'CONFIRMED'."""
    facets = [
        make_facet("fact", "confirmed"),
        make_facet("scale", "confirmed"),
        make_facet("stakeholder_reactions", "confirmed")
    ]
    verdict = synthesize(facets)
    assert verdict.confidence_band == "HIGH"
    assert "CONFIRMED" in verdict.verdict


def test_mixed_confirmed_disputed():
    """2 confirmed + 1 disputed → MODERATE, verdict names disputed facet."""
    facets = [
        make_facet("fact", "confirmed"),
        make_facet("scale", "disputed"),
        make_facet("stakeholder_reactions", "confirmed")
    ]
    verdict = synthesize(facets)
    assert verdict.confidence_band in ["MODERATE", "HIGH"]  # avg = 0.833
    assert "disputed" in verdict.verdict.lower() or "MOSTLY TRUE" in verdict.verdict


def test_contested_mix():
    """1 confirmed + 1 refuted + 1 disputed → CONTESTED."""
    facets = [
        make_facet("fact", "confirmed"),
        make_facet("scale", "refuted"),
        make_facet("stakeholder_reactions", "disputed")
    ]
    verdict = synthesize(facets)
    assert verdict.confidence_band == "CONTESTED"


def test_all_unclear():
    """All unclear → CONTESTED with 'insufficient data'."""
    facets = [
        make_facet("fact", "unclear"),
        make_facet("scale", "unclear"),
        make_facet("stakeholder_reactions", "unclear")
    ]
    verdict = synthesize(facets)
    assert verdict.confidence_band == "CONTESTED"
    assert "INSUFFICIENT" in verdict.verdict


def test_empty_list_raises():
    """Empty list → raises ValueError."""
    with pytest.raises(ValueError):
        synthesize([])


def test_mostly_confirmed():
    """
    Test mostly_confirmed status.

    Why MODERATE not HIGH: avg = (0.75 + 0.75 + 1.0) / 3 = 0.833
    The HIGH threshold is 0.85, so 0.833 falls into MODERATE band.
    mostly_confirmed scores 0.75, confirmed scores 1.0 per synthesizer.py logic.
    """
    facets = [
        make_facet("fact", "mostly_confirmed"),
        make_facet("scale", "mostly_confirmed"),
        make_facet("stakeholder_reactions", "confirmed")
    ]
    verdict = synthesize(facets)
    # avg = (0.75 + 0.75 + 1.0) / 3 = 0.833 → threshold is 0.85 for HIGH, so MODERATE
    assert verdict.confidence_band == "MODERATE"


def test_low_confidence():
    """Test LOW confidence band."""
    facets = [
        make_facet("fact", "disputed"),
        make_facet("scale", "disputed"),
        make_facet("stakeholder_reactions", "disputed")
    ]
    verdict = synthesize(facets)
    # avg = 0.5 → LOW
    assert verdict.confidence_band == "LOW"


def test_source_counts():
    """Test source count aggregation."""
    facets = [
        make_facet("fact", "confirmed", pro_count=5, con_count=1),
        make_facet("scale", "confirmed", pro_count=3, con_count=0),
    ]
    verdict = synthesize(facets)
    assert verdict.sources_examined_total >= 8  # At least pro+con
    assert verdict.quotes_verified_total >= 9  # pro+con verified


def test_refuted_verdict():
    """Any refuted → verdict mentions refuted facet."""
    facets = [
        make_facet("fact", "refuted"),
        make_facet("scale", "confirmed"),
        make_facet("stakeholder_reactions", "confirmed")
    ]
    verdict = synthesize(facets)
    assert "REFUTED" in verdict.verdict or "fact" in verdict.verdict


def test_confidence_inputs_structure():
    """Verify ConfidenceInputs are populated correctly."""
    facets = [
        make_facet("fact", "confirmed"),
        make_facet("scale", "unclear"),
    ]
    verdict = synthesize(facets)
    assert verdict.confidence_inputs.scored_facets_count == 1  # Only "fact" scored
    assert verdict.confidence_inputs.facet_scores["fact"] == 1.0
    assert verdict.confidence_inputs.facet_scores["scale"] is None
