"""Canned LLM responses for offline mode (hero topic: Meta layoffs).

Keeps the pipeline fully runnable with no API keys so teammates can build the
frontend against real event shapes on day one. Keyed by the `mock_key` passed
to llm.json_call.
"""
from __future__ import annotations

from typing import Any, Dict

_MOCKS: Dict[str, Any] = {
    # Fast path (F1): one cheap read -> a provisional Level-0 verdict.
    "fast_path": {
        "early_read": "Likely true, scale disputed",
        "reasoning": "Multiple outlets report a ~5% Meta reduction, but leaked "
                     "figures suggest the real scale may be higher.",
    },
    # Decomposer (F5/F4): fixed facets + settled-fact detection.
    "decompose": {
        "settled_fact": False,
        "settled_reason": None,
        "facet_queries": [
            {
                "facet_key": "fact",
                "pro_query": "Meta workforce reduction 5% official announcement 2026",
                "con_query": "Meta layoffs did not happen denial 2026",
            },
            {
                "facet_key": "scale",
                "pro_query": "Meta layoffs exactly 5% SEC filing memo",
                "con_query": "Meta layoffs more than 5% leaked internal 8-10%",
            },
            {
                "facet_key": "stakeholder_reactions",
                "pro_query": "Meta CEO memo analyst notes layoffs statement",
                "con_query": "Meta employees criticism layoffs reaction",
                "grassroots_query": "reddit.com Meta layoffs employee reaction",
            },
        ],
    },
    # Example of a settled fact, for demoing the F4 short-circuit lane.
    "decompose_settled": {
        "settled_fact": True,
        "settled_reason": "Well-established scientific consensus; not a live controversy.",
        "facet_queries": [
            {
                "facet_key": "fact",
                "pro_query": "evidence earth is round scientific consensus",
                "con_query": "credible evidence earth is not round",
            }
        ],
    },
}


def mock_json(key: str) -> Any:
    if key not in _MOCKS:
        raise KeyError(
            f"No offline mock for '{key}'. Add one in prism/mocks.py "
            f"or set ANTHROPIC_API_KEY to run live."
        )
    return _MOCKS[key]
