import pytest

from prism.settings import get_settings


def _configure(monkeypatch, mode="auto", tavily="", anthropic=""):
    monkeypatch.setenv("PRISM_PIPELINE_MODE", mode)
    monkeypatch.setenv("TAVILY_API_KEY", tavily)
    monkeypatch.setenv("ANTHROPIC_API_KEY", anthropic)
    monkeypatch.setenv("PRISM_CORS_ORIGINS", "http://localhost:3000")
    get_settings.cache_clear()
    return get_settings()


@pytest.mark.parametrize(
    ("tavily", "anthropic", "expected"),
    [("", "", "mock"), ("tvly", "", "tavily"), ("tvly", "anth", "agent")],
)
def test_auto_mode_selection(monkeypatch, tavily, anthropic, expected):
    assert _configure(monkeypatch, tavily=tavily, anthropic=anthropic).pipeline_mode == expected


def test_explicit_live_modes_require_keys(monkeypatch):
    with pytest.raises(ValueError, match="tavily mode requires"):
        _configure(monkeypatch, mode="tavily")
    with pytest.raises(ValueError, match="agent mode requires"):
        _configure(monkeypatch, mode="agent", tavily="tvly")


def test_exact_cors_origins_only(monkeypatch):
    for invalid in ("*", "http://localhost:3000/path", "localhost:3000"):
        monkeypatch.setenv("PRISM_CORS_ORIGINS", invalid)
        monkeypatch.setenv("PRISM_PIPELINE_MODE", "mock")
        get_settings.cache_clear()
        with pytest.raises(ValueError, match="origin"):
            get_settings()


def test_secure_environment_default(monkeypatch):
    monkeypatch.delenv("PRISM_ENV", raising=False)
    assert _configure(monkeypatch).environment == "production"
