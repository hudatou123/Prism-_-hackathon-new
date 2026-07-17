"""Thin Claude wrapper with structured (JSON) output + an offline mock mode.

Two entry points the rest of the pipeline uses:
  - json_call(model, system, user, ...)  -> parsed dict from the model
  - is_offline()                          -> True when no ANTHROPIC_API_KEY

Offline mode returns canned structured responses for the hero topic so the
decomposer and fast path run with zero setup. Swap the provider by editing this
one file (the doc's "vendor-agnostic by design" line applies to the LLM too).
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from .config import FAST_MODEL, MAIN_MODEL, settings

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None  # offline-only environments


def is_offline() -> bool:
    return not settings.has_llm or AsyncAnthropic is None


_client: Optional["AsyncAnthropic"] = None


def _get_client() -> "AsyncAnthropic":
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


_JSON_RE = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)


def extract_json(text: str) -> Any:
    """Tolerant JSON extraction — models sometimes wrap JSON in prose/fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("\n") + 1 :] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        if m:
            return json.loads(m.group(0))
        raise


async def json_call(
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int = 1024,
    mock_key: str = "",
) -> Any:
    """Ask Claude for JSON and return it parsed.

    `fast=True` uses the low-latency model (F1 fast path). `mock_key` selects a
    canned response when offline — see prism/mocks.py.
    """
    if is_offline():
        from .mocks import mock_json
        return mock_json(mock_key)

    model = FAST_MODEL if fast else MAIN_MODEL
    resp = await _get_client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system + "\n\nRespond with ONLY valid JSON. No prose, no code fences.",
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return extract_json(text)
