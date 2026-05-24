"""Triage orchestration service.

Glues together severity, routing, summaries, and the mock integrator,
then persists the result.
"""
from __future__ import annotations

from datetime import datetime

from core.summary_service import build_handoff_summary
from core.database import save_incident
from integrations.mock_integrator import build_mock_payload
from services.routing_service import route_team, escalation_recommendation
from services.severity_service import classify_severity


def run_triage(
    title: str,
    description: str,
    business_area: str,
    system_affected: str,
    impact_level: str,
    urgency: str,
    customer_impact: str,
    submitted_by: str,
    db_path: str | None = None,
) -> dict:
    """Execute the full triage pipeline and persist the incident.

    Returns the result dict ready for template rendering.
    """
    severity, severity_description = classify_severity(impact_level, urgency, customer_impact)
    suggested_team = route_team(title, description)
    escalation = escalation_recommendation(severity)
    handoff = build_handoff_summary(
        title, business_area, system_affected,
        impact_level, urgency, customer_impact,
        severity, severity_description, suggested_team,
    )
    mock = build_mock_payload(
        title, description, business_area, system_affected,
        impact_level, urgency, customer_impact,
        severity, severity_description, suggested_team,
        escalation, handoff, submitted_by,
    )

    record: dict = {
        "title": title,
        "description": description,
        "business_area": business_area,
        "system_affected": system_affected,
        "impact_level": impact_level,
        "urgency": urgency,
        "customer_impact": customer_impact,
        "severity": severity,
        "severity_description": severity_description,
        "suggested_team": suggested_team,
        "escalation_recommendation": escalation,
        "handoff_summary": handoff,
        "mock_payload": str(mock),   # serialised to JSON for SQLite storage
        "submitted_by": submitted_by,
    }
    save_incident(record, db_path)

    return {
        "title": title,
        "description": description,
        "business_area": business_area,
        "system_affected": system_affected,
        "impact_level": impact_level,
        "urgency": urgency,
        "customer_impact": customer_impact,
        "severity": severity,
        "severity_description": severity_description,
        "suggested_team": suggested_team,
        "escalation_recommendation": escalation,
        "handoff_summary": handoff,
        "mock_payload": mock,
    }
