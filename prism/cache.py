"""
Disk-caching decorator for search() and fetch() calls.
Ensures prompt tuning and demo warm-up hit disk instead of live APIs.
"""

import json
import hashlib
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, Callable, Any
from threading import Lock

# Cache directory under repo root
CACHE_ROOT = Path(__file__).parent.parent.parent / ".cache"

# In-process stats tracking
_stats_lock = Lock()
_stats: dict[str, dict[str, int]] = {}


def _get_cache_dir(namespace: str) -> Path:
    """Get cache directory for a namespace, create if needed."""
    cache_dir = CACHE_ROOT / namespace
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate SHA256 cache key from function name + args + kwargs."""
    key_data = f"{func_name}:{repr(args)}:{repr(kwargs)}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def _record_stat(namespace: str, hit: bool):
    """Thread-safe stat recording."""
    with _stats_lock:
        if namespace not in _stats:
            _stats[namespace] = {"hits": 0, "misses": 0}
        if hit:
            _stats[namespace]["hits"] += 1
        else:
            _stats[namespace]["misses"] += 1


def cached(namespace: str, ttl_seconds: Optional[int] = None):
    """
    Decorator that caches function return values to disk under .cache/{namespace}/.
    Key = SHA256 of (function_name + repr(args) + repr(kwargs)).
    Values serialized as JSON (functions must return JSON-serializable data).
    If ttl_seconds is None, cache never expires (hackathon default).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_dir = _get_cache_dir(namespace)
            key = _cache_key(func.__name__, args, kwargs)
            cache_file = cache_dir / f"{key}.json"

            # Check if cache exists and is valid
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        payload = json.load(f)

                    # Check TTL if set
                    if ttl_seconds is not None:
                        cached_at = datetime.fromisoformat(payload['cached_at'])
                        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                        if age > ttl_seconds:
                            # Expired, treat as miss
                            _record_stat(namespace, hit=False)
                            result = func(*args, **kwargs)
                            _write_cache(cache_file, result)
                            return result

                    # Cache hit
                    _record_stat(namespace, hit=True)
                    return payload['value']
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Corrupted cache, treat as miss
                    pass

            # Cache miss — call function and write result
            _record_stat(namespace, hit=False)
            result = func(*args, **kwargs)
            _write_cache(cache_file, result)
            return result

        return wrapper
    return decorator


def _write_cache(cache_file: Path, value: Any):
    """Write cache atomically using temp-file-then-rename pattern."""
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "value": value
    }

    # Write to temp file first, then atomic rename
    fd, temp_path = tempfile.mkstemp(dir=cache_file.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        os.replace(temp_path, cache_file)
    except:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except:
            pass
        raise


def clear_cache(namespace: Optional[str] = None):
    """
    Clear cache files. If namespace is None, clear all namespaces.
    """
    if namespace is None:
        # Clear all
        if CACHE_ROOT.exists():
            for ns_dir in CACHE_ROOT.iterdir():
                if ns_dir.is_dir():
                    for cache_file in ns_dir.glob("*.json"):
                        cache_file.unlink()
    else:
        # Clear specific namespace
        cache_dir = CACHE_ROOT / namespace
        if cache_dir.exists():
            for cache_file in cache_dir.glob("*.json"):
                cache_file.unlink()


def cache_stats() -> dict[str, dict[str, int]]:
    """
    Return in-process cache statistics.
    Returns: {namespace: {"hits": N, "misses": M}}
    """
    with _stats_lock:
        return dict(_stats)
