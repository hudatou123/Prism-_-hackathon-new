"""Fast path -> provisional verdict (F1) — Person A.

Fires immediately on input, in PARALLEL with the decomposer. One cheap search +
one fast-model call produce a Level-0 read in ~2-4s, badged "verifying...".
This is what kills the demo dead-air: something honest on screen in seconds,
later replaced by the synthesized final verdict with a visible swap.

Deliberately cheap and deliberately hedged — it is allowed to be wrong, because
the whole point is that the system visibly upgrades its own answer as evidence
lands.
"""
from __future__ import annotations

from ..config import settings
from ..grounding.interface import Grounding
from ..llm import json_call
from ..schemas import ProvisionalVerdict

_SYSTEM = """You are the fast-path pre-checker in a fact-checker. Given a claim
and a few search snippets, produce:
  - early_read: a SHORT, hedged verdict (max ~10 words), e.g. "Likely true,
    scale disputed" or "Unverified so far".
  - reasoning: ONE sentence explaining the early read, referencing the snippets.
Do not overclaim — this is a preliminary read that will be verified.
Return JSON: {early_read: str, reasoning: str}."""


async def provisional_verdict(claim: str, grounding: Grounding) -> ProvisionalVerdict:
    results = await grounding.search(claim, max_results=settings.fast_path_results)
    snippets = "\n".join(f"- {r.get('title','')}: {r.get('snippet','')}" for r in results[:5])

    data = await json_call(
        _SYSTEM,
        f"CLAIM: {claim}\n\nSEARCH SNIPPETS:\n{snippets or '(none)'}",
        fast=True,          # F1: latency matters here
        max_tokens=120,
        mock_key="fast_path",
    )
    return ProvisionalVerdict(
        claim=claim,
        early_read=data.get("early_read", "Checking..."),
        reasoning=data.get("reasoning", ""),
        sources_so_far=len(results),
    )
