def classify_severity(impact_level, urgency, customer_impact):
    """Return a severity label and human-readable description.

    Rules:
    P1 – high impact OR high urgency with customer impact yes
    P2 – high impact without customer impact, OR medium impact with high urgency
    P3 – medium impact OR medium urgency
    P4 – everything else
    """

    if impact_level == "high" or (urgency == "high" and customer_impact == "yes"):
        return "P1", "Critical – immediate response required. High impact or high urgency with customer impact."

    if impact_level == "high" or (impact_level == "medium" and urgency == "high"):
        return "P2", "Major – prompt response needed. High impact without customer impact, or medium impact with high urgency."

    if impact_level == "medium" or urgency == "medium":
        return "P3", "Moderate – address within the next business cycle. Medium impact or medium urgency."

    return "P4", "Minor – handle during normal operations. Low impact and low urgency."


TEAM_KEYWORDS = {
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


def route_to_team(title, description):
    """Return the best-matching team based on keyword overlap.

    Scans title and description (lower-cased) for keywords.
    Returns the team with the most matching keywords, or Infrastructure Team
    as a fallback when no keywords matched.
    """

    text = (title + " " + description).lower()
    best_team = None
    best_score = 0

    for team, keywords in TEAM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_team = team

    return best_team or "Infrastructure Team"


def build_escalation(severity):
    """Return an escalation recommendation string based on severity."""

    if severity == "P1":
        return (
            "Page the on-call lead immediately. Open a bridge call and notify "
            "the VP of Engineering within 15 minutes. Provide regular updates "
            "every 30 minutes until resolved."
        )
    if severity == "P2":
        return (
            "Notify the on-call engineer and team lead via Slack. Awaite "
            "acknowledgment within 30 minutes. Escalate to VP if not resolved "
            "within 2 hours."
        )
    if severity == "P3":
        return (
            "Create a tracked task in the team's board. Notify the team lead "
            "and assign for next business day."
        )
    return (
        "Log in the team's backlog. Review in the next sprint planning session."
    )


def build_handoff_summary(incident):
    """Build a one-paragraph handoff summary for the owning team."""

    return (
        f"Incident '{incident['title']}' in {incident['business_area']} affecting "
        f"{incident['system_affected']}. Impact: {incident['impact_level']}, "
        f"Urgency: {incident['urgency']}, Customer impact: {incident['customer_impact']}. "
        f"Classified as {incident['severity']} — {incident['severity_description']}. "
        f"Suggested owner: {incident['suggested_team']}."
    )


def build_mock_payload(incident):
    """Build a JSON-serialisable dict representing a ticketing-system payload."""

    return {
        "title": incident["title"],
        "description": incident["description"],
        "business_area": incident["business_area"],
        "system_affected": incident["system_affected"],
        "impact_level": incident["impact_level"],
        "urgency": incident["urgency"],
        "customer_impact": incident["customer_impact"] == "yes",
        "severity": incident["severity"],
        "severity_description": incident["severity_description"],
        "suggested_team": incident["suggested_team"],
        "escalation_recommendation": incident["escalation_recommendation"],
        "handoff_summary": incident["handoff_summary"],
        "submitted_by": incident["submitted_by"],
    }
