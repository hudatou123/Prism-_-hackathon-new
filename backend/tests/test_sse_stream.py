"""No-network tests for the exact named UI SSE contract."""

import json
import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["PRISM_PIPELINE_MODE"] = "mock"
os.environ["PRISM_ENV"] = "test"

from prism.main import app


@pytest.mark.asyncio
async def test_analyze_sse_stream(monkeypatch):
    async def no_delay(_seconds):
        return None

    monkeypatch.setattr("prism.mock_pipeline.asyncio.sleep", no_delay)
    transport = ASGITransport(app=app)
    events = []
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("POST", "/analyze", json={"topic": "Did Meta lay off employees?"}) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            event_type = None
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.split(":", 1)[1].strip()
                elif line.startswith("data:") and event_type:
                    payload = json.loads(line.split(":", 1)[1].strip())
                    events.append((event_type, payload))
                    event_type = None

    names = [name for name, _ in events]
    assert names == [
        "provisional", "facet", "counts", "facet", "counts",
        "facet", "counts", "final", "done",
    ]
    assert all(payload["type"] == name for name, payload in events)
    facets = [payload for name, payload in events if name == "facet"]
    assert [facet["facet"] for facet in facets] == ["fact", "scale", "stakeholders"]
    assert all({"sourcesExamined", "quotesVerified", "quotesTotal"} <= facet.keys()
               for facet in facets)
    assert all(item["verified"] is True for facet in facets for item in facet["evidence"])
    counts = [payload for name, payload in events if name == "counts"]
    assert [item["sourcesExamined"] for item in counts] == sorted(item["sourcesExamined"] for item in counts)
    assert counts[-1]["quotesTotal"] >= counts[-1]["quotesVerified"]


@pytest.mark.asyncio
async def test_event_source_get_shape(monkeypatch):
    async def no_delay(_seconds):
        return None

    monkeypatch.setattr("prism.mock_pipeline.asyncio.sleep", no_delay)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analyze", params={"claim": "Is the Earth round?"})
    assert response.status_code == 200
    assert "event: provisional" in response.text
    assert "event: done" in response.text

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "pipeline_mode": "mock"}


@pytest.mark.asyncio
async def test_cache_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        stats = await client.get("/cache/stats")
        cleared = await client.post("/cache/clear")
    assert stats.status_code == 200
    assert isinstance(stats.json(), dict)
    assert cleared.status_code == 200
    assert cleared.json() == {"status": "cleared"}


@pytest.mark.asyncio
async def test_invalid_topics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_response = await client.post("/analyze", json={"topic": ""})
        get_response = await client.get("/analyze", params={"claim": ""})
    assert post_response.status_code == 422
    assert get_response.status_code == 422


@pytest.mark.asyncio
async def test_cache_clear_is_forbidden_outside_development(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr("prism.main.settings", SimpleNamespace(is_development=False))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/cache/clear")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_stream_error_redacts_internal_details(monkeypatch):
    async def broken_pipeline(_topic):
        if False:
            yield None
        raise RuntimeError("secret-provider-token")

    monkeypatch.setattr("prism.main.run_pipeline", broken_pipeline)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analyze", json={"topic": "test claim"})
    assert response.status_code == 200
    assert 'event: error' in response.text
    assert '"type":"error"' in response.text
    assert "Analysis failed" in response.text
    assert "secret-provider-token" not in response.text
