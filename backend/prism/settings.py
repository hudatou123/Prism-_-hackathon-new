"""Central, validated backend configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env", override=False)

RequestedMode = Literal["auto", "mock", "tavily", "agent"]
ResolvedMode = Literal["mock", "tavily", "agent"]
_VALID_MODES = {"auto", "mock", "tavily", "agent"}


def _cors_origins(value: str) -> tuple[str, ...]:
    origins = tuple(item.strip() for item in value.split(",") if item.strip())
    if not origins or "*" in origins:
        raise ValueError("PRISM_CORS_ORIGINS must list exact origins; wildcard is not allowed")
    for origin in origins:
        try:
            parsed = urlsplit(origin)
            port = parsed.port
        except ValueError as exc:
            raise ValueError(f"invalid CORS origin: {origin}") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError(f"CORS origin must be an exact http(s) origin: {origin}")
    return origins


@dataclass(frozen=True)
class Settings:
    requested_mode: RequestedMode
    pipeline_mode: ResolvedMode
    tavily_api_key: str
    anthropic_api_key: str
    cors_origins: tuple[str, ...]
    environment: str
    fetch_max_bytes: int
    fetch_timeout_seconds: float
    fetch_max_redirects: int

    @property
    def is_development(self) -> bool:
        return self.environment in {"dev", "development", "local", "test"}

def _resolve_mode(requested: RequestedMode, anthropic_key: str, tavily_key: str) -> ResolvedMode:
    if requested == "auto":
        if anthropic_key and tavily_key:
            return "agent"
        if tavily_key:
            return "tavily"
        return "mock"
    if requested == "agent" and not (anthropic_key and tavily_key):
        raise ValueError("agent mode requires ANTHROPIC_API_KEY and TAVILY_API_KEY")
    if requested == "tavily" and not tavily_key:
        raise ValueError("tavily mode requires TAVILY_API_KEY")
    return requested


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_mode = os.getenv("PRISM_PIPELINE_MODE", "auto").strip().lower()
    if raw_mode == "real":
        raise ValueError("PRISM_PIPELINE_MODE=real is unsupported; use auto, mock, tavily, or agent")
    if raw_mode not in _VALID_MODES:
        raise ValueError("PRISM_PIPELINE_MODE must be one of: auto, mock, tavily, agent")

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    requested = raw_mode  # type: ignore[assignment]
    origins = _cors_origins(os.getenv("PRISM_CORS_ORIGINS", "http://localhost:3000"))

    max_bytes = int(os.getenv("PRISM_FETCH_MAX_BYTES", "2000000"))
    timeout = float(os.getenv("PRISM_FETCH_TIMEOUT_SECONDS", "10"))
    redirects = int(os.getenv("PRISM_FETCH_MAX_REDIRECTS", "5"))
    if max_bytes < 1 or timeout <= 0 or redirects < 0:
        raise ValueError("fetch limits must be positive (redirects may be zero)")

    return Settings(
        requested_mode=requested,
        pipeline_mode=_resolve_mode(requested, anthropic_key, tavily_key),
        tavily_api_key=tavily_key,
        anthropic_api_key=anthropic_key,
        cors_origins=origins,
        # Secure default: destructive cache operations require an explicit
        # development-like environment (the example .env sets development).
        environment=os.getenv("PRISM_ENV", "production").strip().lower(),
        fetch_max_bytes=max_bytes,
        fetch_timeout_seconds=timeout,
        fetch_max_redirects=redirects,
    )

