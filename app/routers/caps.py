from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.cap import CapRule, CapRuleCreate, RuleCapCheck, RuleCapResult
from app.services import rule_service, cap_engine

router = APIRouter(prefix="/rules", tags=["Cap Rules"])


@router.post("", response_model=CapRule, status_code=201)
def create_rule(data: CapRuleCreate):
    return rule_service.create_rule(data)


@router.get("", response_model=list[CapRule])
def list_rules(active_only: bool = False):
    return rule_service.list_rules(active_only)


@router.get("/{rule_id}", response_model=CapRule)
def get_rule(rule_id: str):
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}/active")
def set_active(rule_id: str, active: bool):
    rule = rule_service.set_active(rule_id, active)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"rule_id": rule_id, "active": rule.active}


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: str):
    if not rule_service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")


@router.post("/{rule_id}/check", response_model=RuleCapResult)
def check_against_rule(rule_id: str, req: RuleCapCheck):
    """Check a single user against a named rule."""
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if not rule.active:
        return RuleCapResult(
            rule_id=rule_id,
            rule_name=rule.name,
            capped=False,
            current_count=0,
            max_impressions=rule.max_impressions,
            window=rule.window,
            ttl_seconds=0,
        )
    result = cap_engine.check(
        user_id=req.user_id,
        dimension=rule.dimension,
        dimension_id=rule.dimension_id,
        window=rule.window,
        max_impressions=rule.max_impressions,
    )
    return RuleCapResult(
        rule_id=rule_id,
        rule_name=rule.name,
        capped=result.capped,
        current_count=result.current_count,
        max_impressions=result.max_impressions,
        window=result.window,
        ttl_seconds=result.ttl_seconds,
    )
