"""Triage orchestration service.

Glues together severity, routing, summaries, and the mock integrator,
then persists the result.
"""
from __future__ import annotations

from datetime import datetime

from core.summary_service import build_handoff_summary
from integrations.mock_integrator import build_mock_payload
from services.routing_service import route_team, escalation_recommendation
from services.severity_service import classify_severity


def _run_triage_pipeline(title, description, business_area, system_affected,
                         impact_level, urgency, customer_impact, submitted_by):
    """Execute triage heuristics and return the result dict (no DB access)."""
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


def run_triage(title, description, business_area, system_affected,
               impact_level, urgency, customer_impact, submitted_by,
               db_path=None, approval_status="approved"):
    """Execute the full triage pipeline and persist the incident.

    Delegates to _run_triage_pipeline() and then calls save_incident()
    with the ``approval_status`` (so the DB reflects the correct value).
    """
    import json
    from core.database import save_incident

    result = _run_triage_pipeline(
        title, description, business_area, system_affected,
        impact_level, urgency, customer_impact, submitted_by,
    )
    result["submitted_by"] = submitted_by
    result["status"] = approval_status
    db_record = dict(result)
    db_record["mock_payload"] = json.dumps(result["mock_payload"])
    save_incident(db_record, db_path)
    return result
