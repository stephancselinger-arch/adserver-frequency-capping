from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class WindowType(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    LIFETIME = "lifetime"


class CapDimension(str, Enum):
    LINE_ITEM = "line_item"
    CAMPAIGN = "campaign"
    CREATIVE = "creative"
    ADVERTISER = "advertiser"


# ── Rules ─────────────────────────────────────────────────────────────────────

class CapRule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:10]}")
    name: str
    dimension: CapDimension
    dimension_id: str
    window: WindowType
    max_impressions: int
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapRuleCreate(BaseModel):
    name: str
    dimension: CapDimension
    dimension_id: str
    window: WindowType
    max_impressions: int


# ── Check / Record ─────────────────────────────────────────────────────────────

class CapCheck(BaseModel):
    """A single frequency cap check to evaluate."""
    user_id: str
    dimension: CapDimension
    dimension_id: str
    window: WindowType
    max_impressions: int  # inline limit (use when you don't want rule lookup)


class CapResult(BaseModel):
    capped: bool
    current_count: int
    max_impressions: int
    window: WindowType
    dimension: CapDimension
    dimension_id: str
    user_id: str
    ttl_seconds: int  # seconds until this window bucket resets


class BulkCapCheck(BaseModel):
    """Check multiple cap dimensions for a user at once (OpenRTB bid evaluation)."""
    user_id: str
    checks: list[CapCheck]


class BulkCapResult(BaseModel):
    user_id: str
    any_capped: bool            # True if ANY check is capped — quick no-bid signal
    results: list[CapResult]


class ImpressionEvent(BaseModel):
    """Record an impression against one or more cap dimensions."""
    user_id: str
    dimension: CapDimension
    dimension_id: str
    timestamp: Optional[datetime] = None


class BulkImpressionEvent(BaseModel):
    user_id: str
    events: list[ImpressionEvent]


# ── Rule-based check ──────────────────────────────────────────────────────────

class RuleCapCheck(BaseModel):
    """Check a user against a named CapRule."""
    user_id: str
    rule_id: str


class RuleCapResult(BaseModel):
    rule_id: str
    rule_name: str
    capped: bool
    current_count: int
    max_impressions: int
    window: WindowType
    ttl_seconds: int
