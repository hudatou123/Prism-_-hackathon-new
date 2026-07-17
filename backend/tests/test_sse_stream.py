"""
Tests for SSE streaming endpoint using mock pipeline.
"""

import pytest
import os
from httpx import AsyncClient, ASGITransport

# Set mock mode before importing app
os.environ['PRISM_PIPELINE_MODE'] = 'mock'

from prism.main import app


@pytest.mark.asyncio
async def test_analyze_sse_stream():
    """
    POST /analyze with topic and assert sequence:
    provisional_verdict → facet_ready × 3 → final_verdict → done
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        request_body = {"topic": "Did Meta lay off employees?"}

        # Stream SSE events
        events = []
        async with client.stream("POST", "/analyze", json=request_body) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.split("event:")[1].strip()
                elif line.startswith("data:"):
                    data = line.split("data:", 1)[1].strip()
                    if event_type and data:
                        events.append({"event": event_type, "data": data})
                        event_type = None

        # Verify event sequence
        assert len(events) >= 5  # At least: provisional + 3 facets + final + done

        # Check order
        event_types = [e["event"] for e in events]
        assert event_types[0] == "provisional_verdict"
        assert event_types.count("facet_ready") == 3
        assert "final_verdict" in event_types
        assert event_types[-1] == "done"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test /health endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "pipeline_mode" in data


@pytest.mark.asyncio
async def test_cache_stats_endpoint():
    """Test /cache/stats endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_cache_clear_endpoint():
    """Test /cache/clear endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"


@pytest.mark.asyncio
async def test_analyze_invalid_topic():
    """Test /analyze with invalid topic (too short)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analyze", json={"topic": ""})
        assert response.status_code == 422  # Validation error
