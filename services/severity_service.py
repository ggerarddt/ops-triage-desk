"""Severity classification service.

Uses rules defined in core.config with the priority order there.
Does not depend on Flask.
"""
from __future__ import annotations

import core.config as cfg


def classify_severity(impact_level: str, urgency: str, customer_impact: str) -> tuple[str, str]:
    """Return ``(severity_label, description)`` matching the first matching rule."""
    for label, condition, description in cfg.SEVERITY_RULES:
        if _matches(condition, impact_level, urgency, customer_impact):
            return label, description
    # Fallback — should never be reached with complete rules.
    return "P4", cfg.SEVERITY_DESCRIPTIONS["P4"]


def _matches(condition: dict, impact: str, urgency: str, customer_impact: str) -> bool:
    """Return True when *condition* is satisfied by the incident fields."""
    imp_ok = condition["impact"] == "*" or condition["impact"] == impact
    urg_ok = condition["urgency"] == "*" or condition["urgency"] == urgency
    ci_ok = condition["customer_impact"] == "*" or condition["customer_impact"] == customer_impact
    return imp_ok and urg_ok and ci_ok
