"""Shared isolation for SSE-Starlette's loop-bound process event."""

import pytest
from sse_starlette.sse import AppStatus


@pytest.fixture(autouse=True)
def reset_sse_app_status():
    AppStatus.should_exit_event = None
    yield
    AppStatus.should_exit_event = None
