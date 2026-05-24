"""Summary-building service — creates handoff summaries.

Pure function, no Flask, no database.
"""
from __future__ import annotations


def build_handoff_summary(
    title: str,
    business_area: str,
    system_affected: str,
    impact_level: str,
    urgency: str,
    customer_impact: str,
    severity: str,
    severity_description: str,
    suggested_team: str,
) -> str:
    """Build a one-paragraph handoff summary for the owning team."""
    return (
        f"Incident '{title}' in {business_area} affecting "
        f"{system_affected}. Impact: {impact_level}, "
        f"Urgency: {urgency}, Customer impact: {customer_impact}. "
        f"Classified as {severity} — {severity_description}. "
        f"Suggested owner: {suggested_team}."
    )
