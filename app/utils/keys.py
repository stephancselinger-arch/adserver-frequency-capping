from __future__ import annotations

"""
Redis key builder for frequency cap counters.

Key format:
  freq:{dimension}:{dimension_id}:{user_id}:{window_bucket}

Window bucket formats:
  hour:     YYYYMMDDHH          e.g. 2026052509
  day:      YYYYMMDD            e.g. 20260525
  week:     YYYYwWW             e.g. 2026w21
  lifetime: global
"""

from datetime import datetime, timezone

from app.models.cap import WindowType


def _bucket(window: WindowType, ts: datetime) -> str:
    if window == WindowType.HOUR:
        return ts.strftime("%Y%m%d%H")
    if window == WindowType.DAY:
        return ts.strftime("%Y%m%d")
    if window == WindowType.WEEK:
        return ts.strftime("%Yw%W")
    return "global"


def build_key(
    dimension: str,
    dimension_id: str,
    user_id: str,
    window: WindowType,
    ts: datetime | None = None,
) -> str:
    if ts is None:
        ts = datetime.now(timezone.utc)
    bucket = _bucket(window, ts)
    return f"freq:{dimension}:{dimension_id}:{user_id}:{bucket}"
