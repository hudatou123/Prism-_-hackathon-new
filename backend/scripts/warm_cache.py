#!/usr/bin/env python3
"""
Warm Cache Script — Pre-run hero topics through grounding layer so demo runs from cache.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prism.grounding import search, fetch

# Hero topics (matching mock_pipeline)
HERO_QUERIES = [
    "Did Meta lay off 5% of its workforce?",
    "Is Chinese EV BYD outselling Tesla globally?",
    "Did the SEC approve spot Bitcoin ETFs?",
    "Is Twitter/X losing advertisers?",
    "Did OpenAI release GPT-5?",
]


def main():
    print("Warming cache with hero topics...")
    print("=" * 60)

    total_results = 0
    total_fetched = 0

    for i, query in enumerate(HERO_QUERIES, 1):
        print(f"\n[{i}/{len(HERO_QUERIES)}] Searching: {query}")
        results = search(query, max_results=5)
        total_results += len(results)
        print(f"  → Found {len(results)} results")

        # Fetch top 3 URLs
        for j, result in enumerate(results[:3], 1):
            print(f"  [{j}] Fetching: {result.url}")
            text = fetch(result.url)
            if text:
                total_fetched += 1
                print(f"      ✓ Fetched {len(text)} chars")
            else:
                print(f"      ✗ Fetch failed or empty")

    print("\n" + "=" * 60)
    print(f"Cache warm-up complete!")
    print(f"  Total searches: {len(HERO_QUERIES)}")
    print(f"  Total results: {total_results}")
    print(f"  Successfully fetched: {total_fetched} pages")

    # Show cache size
    cache_root = Path(__file__).parent.parent.parent / ".cache"
    if cache_root.exists():
        cache_files = list(cache_root.rglob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        print(f"  Cache size on disk: {total_size / 1024:.1f} KB ({len(cache_files)} files)")


if __name__ == "__main__":
    main()
