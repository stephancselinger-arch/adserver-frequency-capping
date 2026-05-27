from __future__ import annotations

"""
In-memory CapRule registry.

Rules let callers reference a named cap configuration (e.g.
"3 impressions per day for campaign_123") instead of inline limits.
"""

from app.models.cap import CapRule, CapRuleCreate

_rules: dict[str, CapRule] = {}


def create_rule(data: CapRuleCreate) -> CapRule:
    rule = CapRule(**data.model_dump())
    _rules[rule.id] = rule
    return rule


def get_rule(rule_id: str) -> CapRule | None:
    return _rules.get(rule_id)


def list_rules(active_only: bool = False) -> list[CapRule]:
    rules = list(_rules.values())
    if active_only:
        rules = [r for r in rules if r.active]
    return rules


def delete_rule(rule_id: str) -> bool:
    return _rules.pop(rule_id, None) is not None


def set_active(rule_id: str, active: bool) -> CapRule | None:
    rule = _rules.get(rule_id)
    if rule:
        rule.active = active
    return rule
