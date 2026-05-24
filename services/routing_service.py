"""Routing service — team assignment and escalation policy.

No Flask dependency; works with plain strings.
"""
from __future__ import annotations

import core.config as cfg


def route_team(title: str, description: str) -> str:
    """Return the best-matching team based on keyword overlap.

    Scans title + description (lower-cased) for keywords.  Returns the team
    with the most matches, or the configured fallback when nothing matched.
    """
    text = (title + " " + description).lower()
    best_team: str | None = None
    best_score = 0

    for team, keywords in cfg.TEAM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_team = team

    return best_team or cfg.DEFAULT_TEAM


def escalation_recommendation(severity: str) -> str:
    """Look up the escalation steps for the given severity label."""
    return cfg.ESCALATION_POLICY.get(severity, cfg.ESCALATION_POLICY["P4"])
