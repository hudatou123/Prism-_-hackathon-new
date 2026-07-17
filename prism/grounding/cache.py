"""Dev cache + demo safety net (F7).

Every search()/fetch() result is cached to disk keyed by a normalized query/URL.
Two payoffs from §5:
  1. Prompt tuning costs ZERO credits and runs instantly.
  2. Pre-warm the hero topics and the demo survives dead conference wifi.

Person D owns the F7 harness overall; this is the minimal version A needs to
not burn credits while iterating on the decomposer/fast-path.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


class DiskCache:
    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, namespace: str, key: str) -> str:
        digest = hashlib.sha256(_normalize(key).encode("utf-8")).hexdigest()[:32]
        return os.path.join(self.root, f"{namespace}_{digest}.json")

    def get(self, namespace: str, key: str) -> Optional[Any]:
        path = self._path(namespace, key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)["value"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, namespace: str, key: str, value: Any) -> None:
        path = self._path(namespace, key)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"key": key, "value": value}, fh, ensure_ascii=False)
        os.replace(tmp, path)  # atomic — never serve a half-written cache entry
