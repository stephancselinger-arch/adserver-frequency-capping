from __future__ import annotations

"""
Core frequency capping engine.

All public functions are synchronous and storage-agnostic.
The store (memory or Redis) is injected via redis_store.get_store().
"""

from app.models.cap import (
    CapCheck, CapResult, BulkCapCheck, BulkCapResult,
    ImpressionEvent, WindowType, CapDimension,
)
from app.services.redis_store import get_store
from app.utils.keys import build_key


def check(
    user_id: str,
    dimension: CapDimension,
    dimension_id: str,
    window: WindowType,
    max_impressions: int,
) -> CapResult:
    """Return cap status for a single user/dimension/window tuple."""
    store = get_store()
    key = build_key(dimension, dimension_id, user_id, window)
    count = store.get_count(key)
    ttl = store.get_ttl(key, window)
    return CapResult(
        capped=count >= max_impressions,
        current_count=count,
        max_impressions=max_impressions,
        window=window,
        dimension=dimension,
        dimension_id=dimension_id,
        user_id=user_id,
        ttl_seconds=ttl,
    )


def bulk_check(req: BulkCapCheck) -> BulkCapResult:
    """Check multiple cap dimensions for a single user. Used in bid evaluation."""
    results = [
        check(
            user_id=req.user_id,
            dimension=c.dimension,
            dimension_id=c.dimension_id,
            window=c.window,
            max_impressions=c.max_impressions,
        )
        for c in req.checks
    ]
    return BulkCapResult(
        user_id=req.user_id,
        any_capped=any(r.capped for r in results),
        results=results,
    )


def record(
    user_id: str,
    dimension: CapDimension,
    dimension_id: str,
    window: WindowType,
) -> int:
    """Increment the counter for one user/dimension/window. Returns new count."""
    store = get_store()
    key = build_key(dimension, dimension_id, user_id, window)
    return store.increment(key, window)


def record_all_windows(
    user_id: str,
    dimension: CapDimension,
    dimension_id: str,
) -> dict[str, int]:
    """Increment counters across all window types simultaneously."""
    return {
        window.value: record(user_id, dimension, dimension_id, window)
        for window in WindowType
    }


def reset_user(
    user_id: str,
    dimension: CapDimension,
    dimension_id: str,
    window: WindowType,
) -> None:
    """Reset a specific counter — used for testing and admin overrides."""
    store = get_store()
    key = build_key(dimension, dimension_id, user_id, window)
    store.reset(key)
