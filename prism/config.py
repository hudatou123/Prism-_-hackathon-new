"""Central config: fixed facet taxonomy (F5), model tiers, and knobs.

Everything tunable lives here so prompt/scope changes don't require hunting
through the pipeline. The FIXED_FACETS list is the F5 decision made concrete:
the decomposer never invents facets, it only writes queries for these.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


# --- Model tiers -----------------------------------------------------------
# Fast path (F1) wants latency; the decomposer/judge want reasoning.
# Swap these ids freely — see prism/llm.py.
FAST_MODEL = os.getenv("PRISM_FAST_MODEL", "claude-haiku-4-5-20251001")
MAIN_MODEL = os.getenv("PRISM_MAIN_MODEL", "claude-sonnet-5")


# --- Fixed facet taxonomy (F5) --------------------------------------------
@dataclass(frozen=True)
class FacetDef:
    key: str          # stable id used across the A<->D contract
    label: str        # what the UI shows
    icon: str         # Level-1 spectrum icon
    intent: str       # steers the decomposer's query writing
    grassroots: bool = False  # pulls the Reddit sub-bucket (F5 v2)


FIXED_FACETS: List[FacetDef] = [
    FacetDef(
        key="fact",
        label="Fact",
        icon="\U0001F4CA",  # bar chart
        intent="Did the core event actually happen, as literally stated?",
    ),
    FacetDef(
        key="scale",
        label="Scale",
        icon="\U0001F4C8",  # chart up
        intent="Is the magnitude/number in the claim accurate, or disputed?",
    ),
    FacetDef(
        key="stakeholder_reactions",
        label="Stakeholder Reactions",
        icon="\U0001F5E3️",  # speaking head
        intent=(
            "What did named parties publicly say (CEO memo, analyst notes, "
            "employee posts), and how did the grassroots public react?"
        ),
        grassroots=True,  # split into Named (news) + Grassroots (Reddit)
    ),
]

# MVP is 3 facets, not 5 (§10 non-negotiable). Stretch adds more here only.
MVP_FACET_KEYS = [f.key for f in FIXED_FACETS]


@dataclass
class Settings:
    # --- provider selection ---
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    reddit_user_agent: str = field(
        default_factory=lambda: os.getenv("REDDIT_USER_AGENT", "prism/0.1")
    )

    # --- F7 caching (dev cache + demo safety net) ---
    cache_dir: str = field(default_factory=lambda: os.getenv("PRISM_CACHE", ".prism_cache"))
    cache_enabled: bool = field(
        default_factory=lambda: os.getenv("PRISM_CACHE_ENABLED", "1") == "1"
    )

    # --- search budget guardrails (§5) ---
    fast_path_results: int = 5      # 1 cheap search for the provisional verdict
    searches_per_side: int = 2      # Pro 1-2 + Con 1-2 per facet

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_search(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def offline(self) -> bool:
        """No keys -> run against the cached hero-topic fixture (zero-setup demo)."""
        return not (self.has_llm and self.has_search)


settings = Settings()
