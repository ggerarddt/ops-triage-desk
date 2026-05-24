"""Mock integration adapter.

Builds a JSON-serialisable payload for downstream/ticketing integration.
No network I/O.
"""
from __future__ import annotations


def build_mock_payload(
    title: str,
    description: str,
    business_area: str,
    system_affected: str,
    impact_level: str,
    urgency: str,
    customer_impact: str,
    severity: str,
    severity_description: str,
    suggested_team: str,
    escalation_recommendation: str,
    handoff_summary: str,
    submitted_by: str,
) -> dict:
    """Return a serialisable dict representing a ticketing-system payload."""
    return {
        "title": title,
        "description": description,
        "business_area": business_area,
        "system_affected": system_affected,
        "impact_level": impact_level,
        "urgency": urgency,
        "customer_impact": customer_impact == "yes",
        "severity": severity,
        "severity_description": severity_description,
        "suggested_team": suggested_team,
        "escalation_recommendation": escalation_recommendation,
        "handoff_summary": handoff_summary,
        "submitted_by": submitted_by,
    }
