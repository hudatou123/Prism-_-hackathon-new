"""
reddit_fetcher.py — Grassroots reactions from Reddit's public JSON.

For the grassroots half of the Stakeholder Reactions facet (F5 v2).

Trick: append `.json` to any Reddit URL and you get structured JSON
(no API key, no OAuth, no credits — just a User-Agent header).

Graceful degradation: if Reddit is rate-limiting or blocked at the
venue, this returns an empty list. The facet then shows only Named
stakeholders, not a full failure.

Exposed as Claim objects so the same Judge pipeline verifies them —
grep passes trivially because the "quote" IS the comment body from
Reddit's own JSON, but running it keeps the anti-hallucination
story consistent across sub-buckets.
"""
from __future__ import annotations

import httpx

from config import FETCH_TIMEOUT_SECONDS, REDDIT_USER_AGENT
from grounding import search
from schemas import Claim


def _find_thread_urls(topic: str, max_threads: int = 2) -> list[str]:
    """
    Use our normal search() with a reddit.com scope to find relevant threads.
    """
    results = search(f"site:reddit.com {topic}")
    urls: list[str] = []
    for r in results:
        # Only keep actual thread URLs, not user pages or subreddit indexes
        if "/comments/" in r.url:
            urls.append(r.url)
        if len(urls) >= max_threads:
            break
    return urls


def _thread_to_json_url(thread_url: str) -> str:
    """https://reddit.com/r/x/comments/abc/title/ → https://reddit.com/r/x/comments/abc/title/.json"""
    base = thread_url.rstrip("/")
    if base.endswith(".json"):
        return base
    return base + ".json"


def _fetch_top_comments(thread_url: str, max_comments: int = 3) -> list[dict]:
    """
    Hit the .json endpoint and return the top-scored top-level comments.
    Structure: [listing_of_post, listing_of_comments]
    Each comment has: {kind: "t1", data: {body, score, author, permalink}}
    """
    json_url = _thread_to_json_url(thread_url)
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": REDDIT_USER_AGENT},
        ) as client:
            r = client.get(json_url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:  # noqa: BLE001
        print(f"[reddit] fetch failed for {json_url}: {e}")
        return []

    if not isinstance(data, list) or len(data) < 2:
        return []

    comments_listing = data[1]
    children = (comments_listing or {}).get("data", {}).get("children", []) or []

    scored: list[dict] = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        d = child.get("data", {})
        body = (d.get("body") or "").strip()
        if not body or body in ("[deleted]", "[removed]"):
            continue
        scored.append({
            "body": body,
            "score": int(d.get("score", 0)),
            "author": d.get("author", "unknown"),
            "permalink": "https://reddit.com" + d.get("permalink", ""),
        })

    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:max_comments]


def fetch_grassroots(topic: str, max_total: int = 5) -> tuple[list[Claim], list[str]]:
    """
    Return grassroots reactions as Claim objects, plus URLs examined
    (for the Judge's provenance check).

    Fail-safe: returns ([], []) on any error. The facet degrades to
    news-only stakeholder reactions.
    """
    thread_urls = _find_thread_urls(topic, max_threads=2)
    if not thread_urls:
        return [], []

    claims: list[Claim] = []
    urls_examined: list[str] = []

    for turl in thread_urls:
        urls_examined.append(turl)
        for c in _fetch_top_comments(turl, max_comments=3):
            urls_examined.append(c["permalink"])
            statement_preview = c["body"][:120] + ("..." if len(c["body"]) > 120 else "")
            claims.append(Claim(
                statement=f"Reddit user u/{c['author']} (score {c['score']}): {statement_preview}",
                quote=c["body"],
                url=c["permalink"],
                source_title=f"Reddit comment by u/{c['author']}",
            ))
            if len(claims) >= max_total:
                return claims, urls_examined

    return claims, urls_examined
