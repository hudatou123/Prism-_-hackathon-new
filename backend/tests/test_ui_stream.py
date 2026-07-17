from prism.schema import Argument, FacetResult
from prism.ui_stream import CumulativeCounts, facet_event


def _argument(verified: bool, suffix: str) -> Argument:
    return Argument(
        claim=f"Claim {suffix}", quote=f"Literal quote {suffix}",
        url=f"https://news.example/{suffix}", source_domain="news.example",
        quote_verified=verified, source_quality="high",
    )


def test_facet_event_is_verified_only_and_has_exact_counters():
    facet = FacetResult(
        facet_id="stakeholder_reactions", status="unclear", summary="Insufficient data",
        pro_arguments=[_argument(True, "verified"), _argument(False, "rejected")],
        sources_examined=4, quotes_attempted=2, quotes_verified=1,
        con_empty=True, con_searched=2,
    )
    first = facet_event(facet)
    second = facet_event(facet)

    assert first == second
    assert first["type"] == "facet"
    assert first["facet"] == "stakeholders"
    assert first["sourcesExamined"] == 4
    assert first["quotesVerified"] == 1
    assert first["quotesTotal"] == 2
    assert len(first["evidence"]) == 1
    assert first["evidence"][0]["verified"] is True
    assert first["evidence"][0]["id"].startswith("stakeholders-pro-")


def test_counts_are_cumulative_and_use_attempted_as_total():
    counts = CumulativeCounts()
    one = FacetResult(facet_id="fact", status="unclear", summary="One",
                      sources_examined=3, quotes_attempted=2, quotes_verified=1)
    two = FacetResult(facet_id="scale", status="unclear", summary="Two",
                      sources_examined=4, quotes_attempted=3, quotes_verified=2)
    assert counts.add(one) == {"type": "counts", "sourcesExamined": 3,
                               "quotesVerified": 1, "quotesTotal": 2}
    assert counts.add(two) == {"type": "counts", "sourcesExamined": 7,
                               "quotesVerified": 3, "quotesTotal": 5}
