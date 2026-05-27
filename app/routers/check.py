from __future__ import annotations

"""
Real-time check and record endpoints — called on every bid and every win.
"""

from fastapi import APIRouter

from app.models.cap import (
    CapCheck, CapResult,
    BulkCapCheck, BulkCapResult,
    ImpressionEvent, BulkImpressionEvent,
)
from app.services import cap_engine

router = APIRouter(tags=["Frequency Cap"])


@router.post("/check", response_model=CapResult)
def check_cap(req: CapCheck):
    """
    Check whether a user is frequency-capped for a single dimension.
    Call this during bid evaluation — does NOT increment the counter.
    """
    return cap_engine.check(
        user_id=req.user_id,
        dimension=req.dimension,
        dimension_id=req.dimension_id,
        window=req.window,
        max_impressions=req.max_impressions,
    )


@router.post("/check/bulk", response_model=BulkCapResult)
def bulk_check(req: BulkCapCheck):
    """
    Check multiple cap dimensions for a user in one call.
    Returns any_capped=True if ANY dimension is capped (fast no-bid signal).
    """
    return cap_engine.bulk_check(req)


@router.post("/record", status_code=202)
def record_impression(event: ImpressionEvent):
    """
    Record a delivered impression. Increments counters for all window types.
    Call this on win notice (NURL) — after the auction, not during bid eval.
    """
    counts = cap_engine.record_all_windows(
        user_id=event.user_id,
        dimension=event.dimension,
        dimension_id=event.dimension_id,
    )
    return {"user_id": event.user_id, "counts": counts}


@router.post("/record/bulk", status_code=202)
def record_bulk(req: BulkImpressionEvent):
    """Record impressions for multiple dimensions at once (batch win processing)."""
    results = []
    for event in req.events:
        counts = cap_engine.record_all_windows(
            user_id=req.user_id,
            dimension=event.dimension,
            dimension_id=event.dimension_id,
        )
        results.append({"dimension": event.dimension, "dimension_id": event.dimension_id, "counts": counts})
    return {"user_id": req.user_id, "recorded": results}


@router.post("/reset")
def reset_cap(
    user_id: str,
    dimension: str,
    dimension_id: str,
    window: str,
):
    """Admin endpoint: reset a specific counter (testing / override)."""
    from app.models.cap import CapDimension, WindowType
    cap_engine.reset_user(
        user_id=user_id,
        dimension=CapDimension(dimension),
        dimension_id=dimension_id,
        window=WindowType(window),
    )
    return {"reset": True}
