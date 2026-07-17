"""
Tests for Pydantic schema models — the data contract.
"""

import json
import pytest
from prism.schema import (
    Argument, FacetResult, ProvisionalVerdict, FinalVerdict,
    ConfidenceInputs, SSEEvent, AnalyzeRequest
)


def test_argument_basic():
    """Test basic Argument construction."""
    arg = Argument(
        claim="Test claim",
        quote="Test quote from source",
        url="https://example.com/article",
        source_domain="example.com",
        published_date="2024-01-15",
        quote_verified=True,
        source_quality="high"
    )
    assert arg.claim == "Test claim"
    assert arg.quote_verified is True
    assert arg.source_quality == "high"


def test_argument_with_stakeholder():
    """Test Argument with stakeholder fields."""
    arg = Argument(
        claim="CEO statement",
        quote="We are committed to innovation",
        url="https://example.com/press",
        source_domain="example.com",
        quote_verified=True,
        source_quality="high",
        stakeholder_kind="named",
        stakeholder_name="CEO Jane Doe"
    )
    assert arg.stakeholder_kind == "named"
    assert arg.stakeholder_name == "CEO Jane Doe"


def test_argument_json_roundtrip():
    """Test Argument JSON serialization round-trip."""
    arg = Argument(
        claim="Test",
        quote="Quote",
        url="https://example.com",
        source_domain="example.com",
        quote_verified=False,
        source_quality="medium"
    )
    json_str = arg.model_dump_json()
    parsed = json.loads(json_str)
    reconstructed = Argument(**parsed)
    assert reconstructed.claim == arg.claim
    assert reconstructed.quote_verified == arg.quote_verified


def test_facet_result():
    """Test FacetResult construction."""
    facet = FacetResult(
        facet_id="fact",
        status="confirmed",
        summary="This is confirmed",
        pro_arguments=[],
        con_arguments=[],
        sources_examined=10,
        quotes_verified=8
    )
    assert facet.facet_id == "fact"
    assert facet.status == "confirmed"
    assert facet.sources_examined == 10
    assert facet.quotes_attempted == 0
    assert facet.con_empty is False
    assert facet.con_searched == 0


def test_provisional_verdict():
    """Test ProvisionalVerdict."""
    verdict = ProvisionalVerdict(
        verdict="Likely true",
        reasoning="Multiple sources agree",
        sources_so_far=5
    )
    assert verdict.sources_so_far == 5


def test_confidence_inputs():
    """Test ConfidenceInputs."""
    inputs = ConfidenceInputs(
        facet_scores={"fact": 1.0, "scale": 0.75, "stakeholder_reactions": None},
        scored_facets_count=2,
        average_score=0.875,
        sources_agreeing=8,
        sources_total=10
    )
    assert inputs.scored_facets_count == 2
    assert inputs.average_score == 0.875


def test_final_verdict():
    """Test FinalVerdict."""
    verdict = FinalVerdict(
        verdict="CONFIRMED",
        confidence_band="HIGH",
        confidence_inputs=ConfidenceInputs(
            facet_scores={"fact": 1.0, "scale": 1.0, "stakeholder_reactions": 1.0},
            scored_facets_count=3,
            average_score=1.0,
            sources_agreeing=10,
            sources_total=10
        ),
        sources_examined_total=30,
        quotes_verified_total=25
    )
    assert verdict.confidence_band == "HIGH"
    assert verdict.sources_examined_total == 30


def test_sse_event():
    """Test SSEEvent envelope."""
    event = SSEEvent(
        event="facet",
        data={"type": "facet", "facet": "fact"}
    )
    assert event.event == "facet"


def test_analyze_request():
    """Test AnalyzeRequest validation."""
    req = AnalyzeRequest(topic="Did Meta lay off employees?")
    assert req.topic == "Did Meta lay off employees?"

    # Test min_length validation
    with pytest.raises(Exception):  # Pydantic ValidationError
        AnalyzeRequest(topic="")

    # Test max_length validation
    with pytest.raises(Exception):
        AnalyzeRequest(topic="x" * 501)
