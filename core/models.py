"""Domain models used across the triage application."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class User:
    """Lightweight representation of an authenticated user."""
    id: int
    username: str
    role: str


@dataclass(slots=True)
class Incident:
    """Represents raw input from the triage form. Immutable."""
    title: str
    description: str
    business_area: str
    system_affected: str
    impact_level: str
    urgency: str
    customer_impact: str
    submitted_by: str = ""


@dataclass(slots=True)
class TriageResult:
    """Result produced by the triage pipeline."""
    incident: Incident
    severity: str
    severity_description: str
    suggested_team: str
    escalation_recommendation: str
    handoff_summary: str
    mock_payload: dict[str, Any]
    submitted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable dict for templates and the JSON API."""
        return {
            "title": self.incident.title,
            "description": self.incident.description,
            "business_area": self.incident.business_area,
            "system_affected": self.incident.system_affected,
            "impact_level": self.incident.impact_level,
            "urgency": self.incident.urgency,
            "customer_impact": self.incident.customer_impact,
            "severity": self.severity,
            "severity_description": self.severity_description,
            "suggested_team": self.suggested_team,
            "escalation_recommendation": self.escalation_recommendation,
            "handoff_summary": self.handoff_summary,
            "mock_payload": self.mock_payload,
        }
