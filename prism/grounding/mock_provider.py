"""Offline grounding: serves the cached hero-topic fixture (§5 demo safety net).

Active whenever keys are missing. Lets the whole pipeline — decompose, fan-out,
quote-grep, stream — run with zero setup, which is exactly the 0:00-0:45
"build against cached sample data / mock SSE" plan. The fixture page_text
contains the exact quotes the stub agents cite, so the F3 grep really passes.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .cache import DiskCache
from .interface import SearchResult

_FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "fixtures",
    "meta_layoffs.json",
)


class MockGrounding:
    def __init__(self, cache: Optional[DiskCache] = None, fixture_path: str = _FIXTURE):
        self._cache = cache  # unused offline, kept for interface symmetry
        with open(fixture_path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)
        self._by_url: Dict[str, dict] = {s["url"]: s for s in self._data["sources"]}

    # Query words that signal a "con"/counter-evidence search intent. The
    # decomposer's con_query uses these; the offline mock uses them to hand back
    # counter-stance sources so pro vs con actually differ (matching the doc's
    # Level-1 spectrum). Live Tavily needs none of this — it's fixture-only.
    # Terms for which the fixture actually HAS counter-stance sources (they
    # dispute scale/reaction, not whether the event happened).
    _COUNTER_HINTS = (
        "more than", "beyond", "8-10", "higher", "leaked", "leak",
        "disputed", "criticism", "exaggerat",
    )
    # Oppositional framing with NO matching counter source in the fixture. A
    # con_query like "did it happen? denial" hits this -> returns [] -> the
    # facet resolves CONFIRMED (honest "no credible counter-evidence", F4),
    # which is exactly why Fact confirms while Scale disputes.
    _CON_FRAME = ("not ", "denial", "deny", "false", "refute", "debunk", "hoax")

    def _classify(self, q: str) -> str:
        if "reddit.com" in q or "reddit" in q:
            return "grassroots"
        if any(h in q for h in self._COUNTER_HINTS):
            return "counter"
        if any(h in q for h in self._CON_FRAME):
            return "empty"  # oppositional, but nothing credible to show
        return "support"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        want = self._classify(query.lower())
        if want == "empty":
            return []
        out: List[SearchResult] = []
        for s in self._data["sources"]:
            if s.get("stance", "support") != want:
                continue
            out.append(
                {
                    "url": s["url"],
                    "title": s["title"],
                    "snippet": s["snippet"],
                    "published_date": s.get("published_date"),
                }
            )
        return out[:max_results]

    async def fetch(self, url: str) -> str:
        return self._by_url.get(url, {}).get("page_text", "")

    # convenience the offline stubs use to reach fixture-only fields
    def meta(self, url: str) -> dict:
        return self._by_url.get(url, {})

    async def aclose(self) -> None:
        return None
