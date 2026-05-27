from __future__ import annotations

"""
Storage backend for frequency counters.

In dev / test: pure in-memory dict (no Redis needed).
In production: set REDIS_URL=redis://host:6379 to use Redis.

The interface is the same either way, so the engine is storage-agnostic.
"""

import os
import time
from datetime import datetime, timezone

from app.models.cap import WindowType

# ── Window bucket TTLs (seconds) ──────────────────────────────────────────────

_WINDOW_TTL: dict[str, int] = {
    WindowType.HOUR: 3600,
    WindowType.DAY: 86400,
    WindowType.WEEK: 604800,
    WindowType.LIFETIME: 0,   # no expiry
}


# ── In-memory backend (default / test) ────────────────────────────────────────

class _MemoryStore:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._expiry: dict[str, float] = {}   # key -> unix timestamp of expiry (0 = never)

    def _expired(self, key: str) -> bool:
        exp = self._expiry.get(key, 0)
        return exp != 0 and time.time() > exp

    def increment(self, key: str, window: WindowType) -> int:
        if self._expired(key):
            self._counts.pop(key, None)
            self._expiry.pop(key, None)
        self._counts[key] = self._counts.get(key, 0) + 1
        ttl = _WINDOW_TTL[window]
        if ttl and key not in self._expiry:
            self._expiry[key] = time.time() + ttl
        return self._counts[key]

    def get_count(self, key: str) -> int:
        if self._expired(key):
            self._counts.pop(key, None)
            self._expiry.pop(key, None)
            return 0
        return self._counts.get(key, 0)

    def get_ttl(self, key: str, window: WindowType) -> int:
        exp = self._expiry.get(key, 0)
        if exp == 0:
            return 0
        remaining = int(exp - time.time())
        return max(remaining, 0)

    def reset(self, key: str) -> None:
        self._counts.pop(key, None)
        self._expiry.pop(key, None)

    def clear_all(self) -> None:
        self._counts.clear()
        self._expiry.clear()


# ── Redis backend ─────────────────────────────────────────────────────────────

class _RedisStore:
    def __init__(self, url: str) -> None:
        import redis as redis_lib  # type: ignore
        self._r = redis_lib.from_url(url, decode_responses=True)

    def increment(self, key: str, window: WindowType) -> int:
        count = self._r.incr(key)
        ttl = _WINDOW_TTL[window]
        if ttl and self._r.ttl(key) == -1:
            self._r.expire(key, ttl)
        return count

    def get_count(self, key: str) -> int:
        v = self._r.get(key)
        return int(v) if v else 0

    def get_ttl(self, key: str, window: WindowType) -> int:
        ttl = self._r.ttl(key)
        return max(ttl, 0) if ttl >= 0 else 0

    def reset(self, key: str) -> None:
        self._r.delete(key)

    def clear_all(self) -> None:
        self._r.flushdb()


# ── Factory ───────────────────────────────────────────────────────────────────

_store: _MemoryStore | _RedisStore | None = None


def get_store() -> _MemoryStore | _RedisStore:
    global _store
    if _store is None:
        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            _store = _RedisStore(redis_url)
        else:
            _store = _MemoryStore()
    return _store


def reset_store() -> None:
    """Reset for testing — clears in-memory state without destroying the singleton."""
    s = get_store()
    s.clear_all()
