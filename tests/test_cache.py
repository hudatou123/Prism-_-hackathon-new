"""
Tests for cache layer.
"""

import pytest
import time
from pathlib import Path
from prism.cache import cached, clear_cache, cache_stats, CACHE_ROOT


# Test counter to verify function isn't called on cache hit
call_counter = {"count": 0}


@cached(namespace="test")
def expensive_function(x: int) -> int:
    """Test function that increments counter on each call."""
    call_counter["count"] += 1
    return x * 2


def test_cache_miss_then_hit():
    """First call: miss, writes file. Second call: hit, no function invocation."""
    # Reset
    clear_cache("test")
    call_counter["count"] = 0

    # First call — miss
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_counter["count"] == 1

    # Second call with same args — hit
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_counter["count"] == 1  # Function NOT called again


def test_cache_different_args():
    """Different args → different cache files."""
    clear_cache("test")
    call_counter["count"] = 0

    result1 = expensive_function(5)
    result2 = expensive_function(10)

    assert result1 == 10
    assert result2 == 20
    assert call_counter["count"] == 2  # Both calls executed


def test_cache_clear():
    """clear_cache removes files."""
    clear_cache("test")
    call_counter["count"] = 0

    # Prime cache
    expensive_function(5)
    assert call_counter["count"] == 1

    # Clear and call again
    clear_cache("test")
    expensive_function(5)
    assert call_counter["count"] == 2  # Function called again after clear


def test_cache_stats():
    """Test cache statistics tracking."""
    clear_cache("test")
    call_counter["count"] = 0

    # Reset stats by getting baseline
    initial_stats = cache_stats().get("test", {"hits": 0, "misses": 0})

    # Miss
    expensive_function(100)
    stats = cache_stats()
    assert stats["test"]["misses"] >= 1

    # Hit
    expensive_function(100)
    stats = cache_stats()
    assert stats["test"]["hits"] >= 1


def test_cache_file_structure():
    """Verify cache files are created with correct structure."""
    clear_cache("test")
    call_counter["count"] = 0

    expensive_function(42)

    # Check cache directory exists
    cache_dir = CACHE_ROOT / "test"
    assert cache_dir.exists()

    # Check at least one .json file exists
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) >= 1


def test_cache_ttl_expiry():
    """Test TTL expiration (if implemented)."""
    # This test would need a small TTL to be practical
    # For now, just verify the decorator accepts ttl_seconds parameter
    @cached(namespace="test_ttl", ttl_seconds=1)
    def quick_expire(x):
        call_counter["count"] += 1
        return x

    clear_cache("test_ttl")
    call_counter["count"] = 0

    quick_expire(1)
    assert call_counter["count"] == 1

    # Within TTL
    quick_expire(1)
    assert call_counter["count"] == 1  # Cached

    # Wait for expiry
    time.sleep(1.1)
    quick_expire(1)
    assert call_counter["count"] == 2  # Re-executed after expiry
