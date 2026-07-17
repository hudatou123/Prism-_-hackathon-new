"""Layer Decomposer — Agent #1 (Person A). F5 + F4.

Its ONLY jobs (F5 nailed the scope down deliberately):
  1. Decide whether the claim is a settled fact (F4 settled-fact detector). If
     so, flag it so the runner uses a single confirm/refute lane — no debate
     theater around something obviously true.
  2. Write good facet-SPECIFIC search queries for the FIXED facet set. It does
     NOT invent facets; the taxonomy is frozen in config.FIXED_FACETS.

Keeping this agent narrow is what makes it few-shottable in 20 minutes and the
demo consistent across topics.
"""
from __future__ import annotations

from ..config import FIXED_FACETS
from ..llm import json_call
from ..schemas import Decomposition, FacetQueries

_SYSTEM = """You are the Layer Decomposer in an adversarial fact-checker.
You do TWO things and nothing else.

1) SETTLED-FACT CHECK. Decide if the claim is a settled, non-controversial fact
   (e.g. "the earth is round", "water boils at 100C at sea level"). A settled
   fact has overwhelming consensus and no credible live dispute. If it is
   settled, set settled_fact=true and give a one-line settled_reason. Do NOT
   mark a genuinely contested current-events claim as settled.

2) FACET QUERIES. For EACH facet you are given, write a `pro_query` (finds
   evidence the claim is accurate) and a `con_query` (finds the strongest
   counter-evidence). For any facet marked grassroots, also write a
   `grassroots_query` scoped to reddit.com for public reaction. Queries must be
   specific, include entities/numbers/dates from the claim, and be good web
   search strings — not questions."""


def _facet_block() -> str:
    lines = []
    for f in FIXED_FACETS:
        tag = " [grassroots: also write grassroots_query]" if f.grassroots else ""
        lines.append(f"- {f.key} ({f.label}): {f.intent}{tag}")
    return "\n".join(lines)


async def decompose(claim: str) -> Decomposition:
    user = (
        f"CLAIM: {claim}\n\n"
        f"FACETS (fixed — write queries for each, do not add or remove any):\n"
        f"{_facet_block()}\n\n"
        "Return JSON: {settled_fact: bool, settled_reason: str|null, "
        "facet_queries: [{facet_key, pro_query, con_query, grassroots_query?}]}"
    )
    data = await json_call(_SYSTEM, user, fast=False, max_tokens=800, mock_key="decompose")

    fqs = [FacetQueries(**fq) for fq in data.get("facet_queries", [])]
    # Guardrail: never trust the model to keep the taxonomy fixed. Keep only the
    # facets we defined, and don't silently drop one if the model omitted it.
    valid_keys = {f.key for f in FIXED_FACETS}
    fqs = [fq for fq in fqs if fq.facet_key in valid_keys]
    present = {fq.facet_key for fq in fqs}
    for f in FIXED_FACETS:
        if f.key not in present:
            fqs.append(
                FacetQueries(
                    facet_key=f.key,
                    pro_query=f"{claim} {f.label}",
                    con_query=f"{claim} {f.label} disputed OR false",
                    grassroots_query=(f"reddit.com {claim}" if f.grassroots else None),
                )
            )

    return Decomposition(
        claim=claim,
        facet_queries=fqs,
        settled_fact=bool(data.get("settled_fact", False)),
        settled_reason=data.get("settled_reason"),
    )
