"""Per-facet pipe (Plan B) — one deployable unit that runs Pro/Con/Judge.

F2 Plan B is the default assumption: one small .pipe per facet plus one for the
fast path, invoked in parallel by Person D's FastAPI backend, streamed to the
frontend as each resolves. Per-facet pipes also give per-facet traces, which is
the cleaner observability story (§6 F2).

This wraps Person A's facet-execution logic as a RocketRide pipe so the SAME
code runs locally (orchestrator) and deployed (invoke). Person B's live
FacetAgent drops in via default_facet_agent().

Input : {facet_key, pro_query, con_query, grassroots_query?, settled?}
Output: a FacetVerdict as a dict (the A<->D contract).
"""
from __future__ import annotations

from typing import Any, Dict

from prism.agents.procon_judge import default_facet_agent
from prism.config import FIXED_FACETS
from prism.grounding import get_grounding
from prism.rocketride import pipe
from prism.schemas import FacetQueries

_FACET_BY_KEY = {f.key: f for f in FIXED_FACETS}


@pipe("facet")
async def facet_pipe(payload: Dict[str, Any]) -> Dict[str, Any]:
    facet_def = _FACET_BY_KEY[payload["facet_key"]]
    queries = FacetQueries(
        facet_key=payload["facet_key"],
        pro_query=payload["pro_query"],
        con_query=payload["con_query"],
        grassroots_query=payload.get("grassroots_query"),
    )
    grounding = get_grounding()
    try:
        verdict = await default_facet_agent().run(
            facet_def, queries, grounding, settled=payload.get("settled", False)
        )
        return verdict.model_dump()
    finally:
        await grounding.aclose()
