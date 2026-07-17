"""
con_agent.py — The asymmetric Con contract (F4).

This is the hardest, most novel piece of the project. Build this FIRST,
before Pro, so you never confuse "Con is broken because it's missing
opposition" with "Con is broken because I'm asking it to invent opposition."

Public API:
    run_con(facet_query: FacetQuery) -> tuple[ConResult, list[str]]

Behavior:
  - Settled-fact short-circuit: if the Decomposer marks facet_query.is_settled_fact,
    we skip the LLM call entirely and return the abstain result.
  - Otherwise, gather evidence and prompt the model with the F4 asymmetric contract.
  - The LLM may still return `no_credible_counter_evidence_found: true` even for
    non-settled claims. That is the CORRECT behavior when the search results
    genuinely contain no credible opposition.
"""
from __future__ import annotations

from grounding import fetch, search
from llm import call_json
from prompts import CON_SYSTEM, build_user_message
from schemas import Claim, ConResult, FacetQuery


def _gather_evidence(queries: list[str]) -> tuple[list[dict], list[str]]:
    """Identical to pro_agent's version. Kept separate in case Con-specific
    tuning (e.g., different result caps or search modifiers) is added later."""
    seen: set[str] = set()
    evidence: list[dict] = []
    for q in queries:
        for r in search(q):
            if r.url in seen:
                continue
            seen.add(r.url)
            page_text = fetch(r.url)
            evidence.append({
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet,
                "page_text": page_text,
                "published_date": r.published_date,
            })
            if len(evidence) >= 8:
                break
        if len(evidence) >= 8:
            break
    return evidence, list(seen)


def run_con(facet_query: FacetQuery) -> tuple[ConResult, list[str]]:
    """
    Run the Con agent for one facet.

    Returns (ConResult, urls_examined).

    The settled-fact short-circuit is a HARD SKIP — no LLM call, no cost.
    """
    # F4 short-circuit: Decomposer said this is settled.
    if facet_query.is_settled_fact:
        return (
            ConResult(
                no_credible_counter_evidence_found=True,
                reason="Decomposer classified this as a settled fact; no debate lane run.",
                claims=[],
            ),
            [],
        )

    evidence, urls_examined = _gather_evidence(facet_query.queries)

    if not evidence:
        return (
            ConResult(
                no_credible_counter_evidence_found=True,
                reason="No search results returned for counter-evidence queries.",
                claims=[],
            ),
            urls_examined,
        )

    user_msg = build_user_message(
        topic=facet_query.topic,
        facet_name=facet_query.facet_name,
        evidence=evidence,
    )

    try:
        raw = call_json(system=CON_SYSTEM, user=user_msg)
    except ValueError as e:
        print(f"[con_agent] LLM JSON failure: {e}")
        # Fail-safe: if the model output is broken, treat as no-evidence-found
        # rather than surfacing garbage.
        return (
            ConResult(
                no_credible_counter_evidence_found=True,
                reason=f"Con agent output could not be parsed; treating as no evidence found. ({e})",
                claims=[],
            ),
            urls_examined,
        )

    # Read the abstain flag
    abstained = bool(raw.get("no_credible_counter_evidence_found", False))
    reason = raw.get("reason", "") or ""

    claims: list[Claim] = []
    if not abstained:
        for c in raw.get("claims", []) or []:
            try:
                claims.append(Claim(**c))
            except Exception as e:  # noqa: BLE001
                print(f"[con_agent] skipping malformed claim: {e}")
                continue

    # Coherence check: if the model said "abstain" but also returned claims,
    # trust the flag and drop the claims. If it said "not abstain" but returned
    # zero claims, upgrade to abstain (honest empty result).
    if abstained:
        claims = []
    elif not claims:
        abstained = True
        reason = reason or "Model returned no claims; treating as no credible counter-evidence."

    return (
        ConResult(
            no_credible_counter_evidence_found=abstained,
            reason=reason,
            claims=claims,
        ),
        urls_examined,
    )
