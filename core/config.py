"""Configuration for the triage system.

Everything that can reasonably change without code edits lives here:
severity descriptions, team keyword mappings, default team, seed users
and seed example incidents.
"""
from dataclasses import dataclass

from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# Severity classifications
# ---------------------------------------------------------------------------

SEVERITY_DESCRIPTIONS: dict[str, str] = {
    "P1": "Critical – immediate response required. High impact or high urgency with customer impact.",
    "P2": "Major – prompt response needed. High impact without customer impact, or medium impact with high urgency.",
    "P3": "Moderate – address within the next business cycle. Medium impact or medium urgency.",
    "P4": "Minor – handle during normal operations. Low impact and low urgency.",
}

# Priority-ordered list so we can iterate consistently.
SEVERITY_RULES: list[tuple[str, dict[str, str], str]] = [
    # (label, condition, description)
    (
        "P1",
        {"impact": "high", "urgency": "*", "customer_impact": "*"},
        SEVERITY_DESCRIPTIONS["P1"],
    ),
    (
        "P1",
        {"impact": "*", "urgency": "high", "customer_impact": "yes"},
        SEVERITY_DESCRIPTIONS["P1"],
    ),
    (
        "P2",
        {"impact": "high", "urgency": "*", "customer_impact": "no"},
        SEVERITY_DESCRIPTIONS["P2"],
    ),
    (
        "P2",
        {"impact": "medium", "urgency": "high", "customer_impact": "*"},
        SEVERITY_DESCRIPTIONS["P2"],
    ),
    (
        "P3",
        {"impact": "medium", "urgency": "*", "customer_impact": "*"},
        SEVERITY_DESCRIPTIONS["P3"],
    ),
    (
        "P3",
        {"impact": "*", "urgency": "medium", "customer_impact": "*"},
        SEVERITY_DESCRIPTIONS["P3"],
    ),
]

# ---------------------------------------------------------------------------
# Routing configuration
# ---------------------------------------------------------------------------

TEAM_KEYWORDS: dict[str, list[str]] = {
    "API Integration Team": [
        "api", "rest", "endpoint", "http", "502", "503", "gateway",
        "integration", "webhook", "oauth", "authentication", "rate limit",
    ],
    "Data Platform Team": [
        "pipeline", "etl", "data warehouse", "warehouse", "database",
        "sql", "dataset", "schema", "migration", "transform", "batch",
        "disk capacity", "storage",
    ],
    "Customer Operations Team": [
        "customer", "user", "client", "account", "support",
        "billing", "subscription", "onboarding", "ticket",
    ],
    "Infrastructure Team": [
        "server", "host", "vm", "disk", "cpu", "memory",
        "network", "dns", "load balancer", "cluster", "capacity",
        "uptime", "outage", "deployment", "infra",
    ],
}

DEFAULT_TEAM = "Infrastructure Team"

# ---------------------------------------------------------------------------
# Escalation policy
# ---------------------------------------------------------------------------

ESCALATION_POLICY: dict[str, str] = {
    "P1": (
        "Page the on-call lead immediately. Open a bridge call and notify "
        "the VP of Engineering within 15 minutes. Provide regular updates "
        "every 30 minutes until resolved."
    ),
    "P2": (
        "Notify the on-call engineer and team lead via Slack. Await "
        "acknowledgment within 30 minutes. Escalate to VP if not resolved "
        "within 2 hours."
    ),
    "P3": (
        "Create a tracked task in the team's board. Notify the team lead "
        "and assign for next business day."
    ),
    "P4": (
        "Log in the team's backlog. Review in the next sprint planning session."
    ),
}

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_USERS: list[tuple[str, str, str]] = [
    ("operator1", generate_password_hash("ChangeMe123!"), "operator"),
    ("operator2", generate_password_hash("ChangeMe123!"), "operator"),
    ("supervisor1", generate_password_hash("ChangeMe123!"), "supervisor"),
]

SEED_INCIDENTS: list[tuple[str, str, str, str, str, str, str]] = [
    (
        "Benefits API - Intermittent 502 Errors",
        "The benefits REST API is returning intermittent HTTP 502 "
        "Bad Gateway errors during peak hours. All endpoints are affected.",
        "Public Administration",
        "Benefits API",
        "high",
        "high",
        "yes",
    ),
    (
        "Mail Sorting ETL Pipeline Stalled",
        "The nightly ETL pipeline for the mail sorting system has been "
        "stalled for 4 hours. No records are being processed.",
        "Postal Service",
        "Mail Sorting Data Pipeline",
        "medium",
        "high",
        "no",
    ),
    (
        "Data Warehouse Disk Capacity Warning",
        "The national research data warehouse is at 92% disk capacity. "
        "If capacity is not freed, ingestion will fail within 48 hours.",
        "National Research Center",
        "Data Warehouse",
        "high",
        "medium",
        "no",
    ),
]
