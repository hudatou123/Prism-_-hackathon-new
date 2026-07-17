#!/usr/bin/env python3
"""
Burst Test Script — Measure search provider rate limit and latency.
"""

import sys
import time
import asyncio
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os

from prism.grounding import search
from prism.settings import get_settings

TAVILY_API_KEY = get_settings().tavily_api_key


async def burst_search(query: str, index: int) -> dict:
    """Single search call with timing."""
    start = time.time()
    try:
        # Force bypass cache by using unique query
        results = search(f"{query} {index}", max_results=3)
        elapsed = time.time() - start
        return {
            "index": index,
            "success": True,
            "elapsed": elapsed,
            "result_count": len(results)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "index": index,
            "success": False,
            "elapsed": elapsed,
            "error": str(e)
        }


async def main():
    print("Burst Test — Search Provider Rate Limit & Latency")
    print("=" * 60)

    if not TAVILY_API_KEY:
        print("TAVILY_API_KEY is not set in backend/.env; live burst test skipped")
        raise SystemExit(2)
    print("TAVILY_API_KEY found — testing live provider")

    print(f"\nFiring 10 parallel search calls...")
    print("-" * 60)

    start_wall = time.time()

    # Fire 10 parallel searches
    tasks = [burst_search("test query", i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    wall_time = time.time() - start_wall

    # Analyze results
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    print(f"\n{'='*60}")
    print("Results:")
    print(f"  Total wall time: {wall_time:.2f}s")
    print(f"  Successes: {len(successes)}/10")
    print(f"  Failures: {len(failures)}/10")

    if successes:
        latencies = [r["elapsed"] for r in successes]
        print(f"\nLatency statistics:")
        print(f"  p50: {statistics.median(latencies):.2f}s")
        print(f"  p95: {statistics.quantiles(latencies, n=20)[18]:.2f}s" if len(latencies) > 5 else f"  p95: N/A (insufficient data)")
        print(f"  min: {min(latencies):.2f}s")
        print(f"  max: {max(latencies):.2f}s")
        print(f"  mean: {statistics.mean(latencies):.2f}s")

    if failures:
        print(f"\nErrors:")
        for f in failures[:3]:  # Show first 3
            print(f"  [{f['index']}] {f.get('error', 'Unknown error')}")

    # Exit code
    error_rate = len(failures) / 10
    print(f"\n{'='*60}")
    if error_rate > 0.2:
        print(f"⚠️  ERROR: {error_rate*100:.0f}% error rate exceeds 20% threshold")
        sys.exit(1)
    else:
        print(f"✓ PASS: {error_rate*100:.0f}% error rate within acceptable range")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
