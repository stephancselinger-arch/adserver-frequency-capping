from __future__ import annotations

import pytest

from app.models.cap import CapDimension, WindowType, BulkCapCheck, CapCheck
from app.services import cap_engine
from app.services.redis_store import reset_store


def setup_function():
    reset_store()


# ── Basic check / record ──────────────────────────────────────────────────────

def test_not_capped_initially():
    result = cap_engine.check("usr_1", CapDimension.LINE_ITEM, "li_1", WindowType.DAY, 3)
    assert not result.capped
    assert result.current_count == 0


def test_becomes_capped_at_limit():
    for _ in range(3):
        cap_engine.record("usr_1", CapDimension.LINE_ITEM, "li_1", WindowType.DAY)
    result = cap_engine.check("usr_1", CapDimension.LINE_ITEM, "li_1", WindowType.DAY, 3)
    assert result.capped
    assert result.current_count == 3


def test_not_capped_below_limit():
    cap_engine.record("usr_2", CapDimension.CAMPAIGN, "cmp_1", WindowType.DAY)
    cap_engine.record("usr_2", CapDimension.CAMPAIGN, "cmp_1", WindowType.DAY)
    result = cap_engine.check("usr_2", CapDimension.CAMPAIGN, "cmp_1", WindowType.DAY, 3)
    assert not result.capped
    assert result.current_count == 2


def test_check_does_not_increment():
    cap_engine.check("usr_3", CapDimension.CREATIVE, "cr_1", WindowType.HOUR, 5)
    cap_engine.check("usr_3", CapDimension.CREATIVE, "cr_1", WindowType.HOUR, 5)
    result = cap_engine.check("usr_3", CapDimension.CREATIVE, "cr_1", WindowType.HOUR, 5)
    assert result.current_count == 0


# ── Window isolation ──────────────────────────────────────────────────────────

def test_windows_are_independent():
    for _ in range(5):
        cap_engine.record("usr_4", CapDimension.LINE_ITEM, "li_2", WindowType.HOUR)
    # Hour is capped but day should still be independent
    hour_result = cap_engine.check("usr_4", CapDimension.LINE_ITEM, "li_2", WindowType.HOUR, 5)
    day_result = cap_engine.check("usr_4", CapDimension.LINE_ITEM, "li_2", WindowType.DAY, 10)
    assert hour_result.capped
    assert not day_result.capped


# ── User isolation ────────────────────────────────────────────────────────────

def test_different_users_are_isolated():
    for _ in range(3):
        cap_engine.record("usr_a", CapDimension.CAMPAIGN, "cmp_2", WindowType.DAY)
    result_a = cap_engine.check("usr_a", CapDimension.CAMPAIGN, "cmp_2", WindowType.DAY, 3)
    result_b = cap_engine.check("usr_b", CapDimension.CAMPAIGN, "cmp_2", WindowType.DAY, 3)
    assert result_a.capped
    assert not result_b.capped


# ── Bulk check ────────────────────────────────────────────────────────────────

def test_bulk_check_none_capped():
    req = BulkCapCheck(
        user_id="usr_bulk",
        checks=[
            CapCheck(user_id="usr_bulk", dimension=CapDimension.LINE_ITEM, dimension_id="li_b1", window=WindowType.DAY, max_impressions=5),
            CapCheck(user_id="usr_bulk", dimension=CapDimension.CAMPAIGN, dimension_id="cmp_b1", window=WindowType.DAY, max_impressions=10),
        ],
    )
    result = cap_engine.bulk_check(req)
    assert not result.any_capped
    assert len(result.results) == 2


def test_bulk_check_one_capped_flags_any():
    cap_engine.record("usr_bulk2", CapDimension.LINE_ITEM, "li_b2", WindowType.DAY)
    cap_engine.record("usr_bulk2", CapDimension.LINE_ITEM, "li_b2", WindowType.DAY)
    req = BulkCapCheck(
        user_id="usr_bulk2",
        checks=[
            CapCheck(user_id="usr_bulk2", dimension=CapDimension.LINE_ITEM, dimension_id="li_b2", window=WindowType.DAY, max_impressions=2),
            CapCheck(user_id="usr_bulk2", dimension=CapDimension.CAMPAIGN, dimension_id="cmp_b2", window=WindowType.DAY, max_impressions=10),
        ],
    )
    result = cap_engine.bulk_check(req)
    assert result.any_capped
    assert result.results[0].capped
    assert not result.results[1].capped


# ── Record all windows ────────────────────────────────────────────────────────

def test_record_all_windows_increments_each():
    counts = cap_engine.record_all_windows("usr_aw", CapDimension.ADVERTISER, "adv_1")
    assert counts["hour"] == 1
    assert counts["day"] == 1
    assert counts["week"] == 1
    assert counts["lifetime"] == 1


def test_record_all_windows_accumulates():
    cap_engine.record_all_windows("usr_aw2", CapDimension.CAMPAIGN, "cmp_aw")
    cap_engine.record_all_windows("usr_aw2", CapDimension.CAMPAIGN, "cmp_aw")
    counts = cap_engine.record_all_windows("usr_aw2", CapDimension.CAMPAIGN, "cmp_aw")
    assert counts["lifetime"] == 3


# ── Reset ─────────────────────────────────────────────────────────────────────

def test_reset_clears_counter():
    cap_engine.record("usr_r", CapDimension.LINE_ITEM, "li_r", WindowType.DAY)
    cap_engine.record("usr_r", CapDimension.LINE_ITEM, "li_r", WindowType.DAY)
    cap_engine.reset_user("usr_r", CapDimension.LINE_ITEM, "li_r", WindowType.DAY)
    result = cap_engine.check("usr_r", CapDimension.LINE_ITEM, "li_r", WindowType.DAY, 5)
    assert result.current_count == 0
