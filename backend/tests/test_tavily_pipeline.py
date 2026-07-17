import itertools

import pytest

from prism.grounding import SearchResult
from prism.schema import FacetResult, ProvisionalVerdict
from prism import tavily_pipeline


@pytest.mark.asyncio
async def test_tavily_pipeline_uses_fixed_facets_and_real_counters(monkeypatch):
    sequence = itertools.count()

    def fake_search(_query, _max_results):
        number = next(sequence)
        return [SearchResult(url=f"https://news.example/{number}",
                             title=f"Result {number}", snippet="relevant evidence")]

    def fake_fetch(url):
        return f"This fetched article contains relevant evidence for {url}."

    monkeypatch.setattr(tavily_pipeline, "search", fake_search)
    monkeypatch.setattr(tavily_pipeline, "fetch", fake_fetch)
    output = [item async for item in tavily_pipeline.run("A claim")]

    assert isinstance(output[0], ProvisionalVerdict)
    assert output[0].sources_so_far == 0
    facets = [item for item in output if isinstance(item, FacetResult)]
    assert {facet.facet_id for facet in facets} == {
        "fact", "scale", "stakeholder_reactions",
    }
    assert all(facet.sources_examined == 3 for facet in facets)
    assert all(facet.quotes_attempted == 3 for facet in facets)
    assert all(facet.quotes_verified == 3 for facet in facets)


@pytest.mark.asyncio
async def test_tavily_failure_does_not_fall_back_to_mock(monkeypatch):
    def failed_search(*_args):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(tavily_pipeline, "search", failed_search)
    stream = tavily_pipeline.run("A claim")
    assert isinstance(await anext(stream), ProvisionalVerdict)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await anext(stream)
