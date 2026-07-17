"""The two functions §5 promises. Everything else is an implementation detail."""
from __future__ import annotations

from typing import List, Optional, Protocol, TypedDict


class SearchResult(TypedDict, total=False):
    url: str
    title: str
    snippet: str
    published_date: Optional[str]


class Grounding(Protocol):
    """Provider-agnostic grounding. Async so the fan-out can fire concurrently."""

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Return web results with real URLs. 1 basic search ~= 1 Tavily credit."""
        ...

    async def fetch(self, url: str) -> str:
        """Return clean page text — the substrate the F3 quote-grep runs against."""
        ...

    async def aclose(self) -> None:
        """Release any pooled connections."""
        ...
