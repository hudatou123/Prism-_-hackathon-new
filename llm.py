"""
llm.py — Thin Anthropic wrapper with reliable JSON output.

Person B: never call anthropic.Anthropic() directly from an agent.
Use call_json() so JSON parsing failures are handled centrally.

Key trick: on parse failure we ask the model to fix its own output
(one retry only). This eliminates ~95% of "oh no it added ```json fences"
errors that would otherwise kill your demo at hour 5.
"""
from __future__ import annotations

import json
import re
from typing import Any

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, MODEL_MAIN

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not set — put it in .env")
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> str:
    """Pull JSON out of text that might have markdown fences or prose."""
    # ```json ... ``` fences
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    # First balanced-looking { ... } or [ ... ]
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        if start != -1:
            end = text.rfind(closer)
            if end > start:
                return text[start : end + 1]
    return text.strip()


def call_json(
    system: str,
    user: str,
    model: str = MODEL_MAIN,
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """
    Call the LLM and return a parsed dict.

    Runs up to 2 attempts. On JSON parse failure, we send the malformed
    output back to the model with "return ONLY valid JSON matching the
    schema" and try once more. If that fails too, raises ValueError.

    Temperature is 0.2 by default — we want deterministic, faithful
    extraction, not creative writing. Do not raise this above 0.3
    for Pro/Con work.
    """
    client = _get_client()

    def _once(messages):
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        # Concatenate all text blocks (Claude may return multiple)
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        return text

    # First attempt
    raw = _once([{"role": "user", "content": user}])
    try:
        return json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        pass

    # Repair attempt: hand the model back its malformed output and demand JSON
    repair_user = (
        "Your previous response was not valid JSON. Return ONLY the JSON object "
        "described in the original instructions. No prose, no markdown fences, no "
        "leading/trailing text. Here was your response:\n\n" + raw
    )
    raw2 = _once([
        {"role": "user", "content": user},
        {"role": "assistant", "content": raw},
        {"role": "user", "content": repair_user},
    ])
    try:
        return json.loads(_extract_json(raw2))
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM produced un-parseable JSON twice: {raw2[:400]}") from e
