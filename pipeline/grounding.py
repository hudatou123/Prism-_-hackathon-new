"""
grounding.py — Provider-agnostic search + fetch, with dev-cache.

Person B: you call search() and fetch() everywhere. You should never
touch Tavily or httpx directly from an agent. If Person D swaps in a
different provider, your agent code doesn't change.

Cache design (F7): every result is JSON-serialized to disk keyed by a
hash of the query/URL. Prompt tuning runs at zero credit cost and zero
latency. Pre-warm the cache with hero topics before demo (F7).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import httpx
import trafilatura
from tavily import TavilyClient

from config import (
    CACHE_DIR,
    FETCH_MAX_BYTES,
    FETCH_TIMEOUT_SECONDS,
    SEARCH_MAX_RESULTS,
    TAVILY_API_KEY,
)


@dataclass
class SearchResult:
    url: str
    title: str = ""
    snippet: str = ""
    published_date: Optional[str] = None


# ── Cache primitives ────────────────────────────────────────────────────
def _cache_key(kind: str, payload: str) -> Path:
    """Deterministic on-disk key. `kind` separates search vs fetch."""
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    d = CACHE_DIR / kind
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{h}.json"


def _cache_read(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def _cache_write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


# ── Search ──────────────────────────────────────────────────────────────
_tavily: Optional[TavilyClient] = None


def _get_tavily() -> TavilyClient:
    global _tavily
    if _tavily is None:
        if not TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY not set — put it in .env")
        _tavily = TavilyClient(api_key=TAVILY_API_KEY)
    return _tavily


def search(query: str, max_results: int = SEARCH_MAX_RESULTS) -> list[SearchResult]:
    """
    Live web search. Cached to disk on first call per query.

    Returns a list of SearchResult. Never raises on network errors —
    returns empty list. Callers must handle empty gracefully (that
    triggers the honest "no evidence" path).
    """
    key = _cache_key("search", f"{query}|{max_results}")
    cached = _cache_read(key)
    if cached is not None:
        return [SearchResult(**r) for r in cached]

    try:
        resp = _get_tavily().search(query=query, max_results=max_results)
        raw = resp.get("results", [])
        results = [
            SearchResult(
                url=r.get("url", ""),
                title=r.get("title", ""),
                snippet=r.get("content", "") or r.get("snippet", ""),
                published_date=r.get("published_date"),
            )
            for r in raw
            if r.get("url")
        ]
    except Exception as e:  # noqa: BLE001
        print(f"[search] error: {e}")
        results = []

    _cache_write(key, [asdict(r) for r in results])
    return results


# ── Fetch ───────────────────────────────────────────────────────────────
def fetch(url: str) -> str:
    """
    Fetch a URL and return clean article text (trafilatura extraction).

    Cached forever per URL (dev cache — do NOT ship this to production
    as-is; a real system would want TTLs).

    Returns empty string on any failure. The Judge treats empty text as
    a failed provenance check.
    """
    key = _cache_key("fetch", url)
    cached = _cache_read(key)
    if cached is not None:
        return cached.get("text", "")

    text = ""
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Prism-HackwithSeattle)"},
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            # Guard against downloading huge PDFs / videos
            content = r.content[:FETCH_MAX_BYTES]
            html = content.decode(r.encoding or "utf-8", errors="replace")
            extracted = trafilatura.extract(html, include_comments=False)
            text = extracted or ""
    except Exception as e:  # noqa: BLE001
        print(f"[fetch] error {url}: {e}")
        text = ""

    _cache_write(key, {"url": url, "text": text})
    return text


# ── Cache utilities (for tests / demo prep) ─────────────────────────────
def cache_stats() -> dict:
    """How many things are cached. Useful before demo to confirm pre-warm."""
    return {
        "searches": len(list((CACHE_DIR / "search").glob("*.json"))) if (CACHE_DIR / "search").exists() else 0,
        "fetches": len(list((CACHE_DIR / "fetch").glob("*.json"))) if (CACHE_DIR / "fetch").exists() else 0,
    }


def clear_cache() -> None:
    """Nuke the cache. Use during setup to prove a run is genuinely live."""
    for kind in ("search", "fetch"):
        d = CACHE_DIR / kind
        if d.exists():
            for f in d.glob("*.json"):
                f.unlink()
