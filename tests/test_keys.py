from __future__ import annotations

from datetime import datetime, timezone

from app.models.cap import WindowType
from app.utils.keys import build_key, _bucket


def _dt(year: int, month: int, day: int, hour: int = 9) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def test_hour_bucket_format():
    ts = _dt(2026, 5, 25, 9)
    assert _bucket(WindowType.HOUR, ts) == "2026052509"


def test_day_bucket_format():
    ts = _dt(2026, 5, 25)
    assert _bucket(WindowType.DAY, ts) == "20260525"


def test_week_bucket_format():
    ts = _dt(2026, 5, 25)
    bucket = _bucket(WindowType.WEEK, ts)
    assert bucket.startswith("2026w")


def test_lifetime_bucket():
    ts = _dt(2026, 5, 25)
    assert _bucket(WindowType.LIFETIME, ts) == "global"


def test_key_structure():
    ts = _dt(2026, 5, 25, 9)
    key = build_key("line_item", "li_abc", "usr_123", WindowType.HOUR, ts)
    assert key == "freq:line_item:li_abc:usr_123:2026052509"


def test_same_hour_same_key():
    ts1 = datetime(2026, 5, 25, 9, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 25, 9, 59, 59, tzinfo=timezone.utc)
    k1 = build_key("campaign", "cmp_1", "usr_1", WindowType.HOUR, ts1)
    k2 = build_key("campaign", "cmp_1", "usr_1", WindowType.HOUR, ts2)
    assert k1 == k2


def test_different_hours_different_keys():
    ts1 = datetime(2026, 5, 25, 9, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 25, 10, 0, 0, tzinfo=timezone.utc)
    k1 = build_key("campaign", "cmp_1", "usr_1", WindowType.HOUR, ts1)
    k2 = build_key("campaign", "cmp_1", "usr_1", WindowType.HOUR, ts2)
    assert k1 != k2


def test_different_users_different_keys():
    ts = _dt(2026, 5, 25)
    k1 = build_key("line_item", "li_1", "usr_A", WindowType.DAY, ts)
    k2 = build_key("line_item", "li_1", "usr_B", WindowType.DAY, ts)
    assert k1 != k2
