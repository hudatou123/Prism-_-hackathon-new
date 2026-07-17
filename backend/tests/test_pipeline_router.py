import sys
from types import ModuleType, SimpleNamespace

import pytest

from prism import pipeline_router
from prism.schema import ProvisionalVerdict


@pytest.mark.asyncio
async def test_mock_route_does_not_import_agent_pipeline(monkeypatch):
    fake_mock = ModuleType("prism.mock_pipeline")

    async def fake_run(_topic):
        yield ProvisionalVerdict(verdict="Fixture", reasoning="Fixture", sources_so_far=0)

    fake_mock.run = fake_run
    monkeypatch.setitem(sys.modules, "prism.mock_pipeline", fake_mock)
    monkeypatch.delitem(sys.modules, "prism.agent_pipeline", raising=False)
    monkeypatch.setattr(pipeline_router, "get_settings",
                        lambda: SimpleNamespace(pipeline_mode="mock"))

    output = [item async for item in pipeline_router.run_pipeline("claim")]
    assert output[0].verdict == "Fixture"
    assert "prism.agent_pipeline" not in sys.modules
