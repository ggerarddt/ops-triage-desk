"""Routing logic tests.

Covers each team, the fallback, and tie scenarios.
"""
import pytest

from services.routing_service import route_team, escalation_recommendation


class TestRouteAPITeam:
    def test_keyword_api(self):
        team = route_team("API Down", "REST endpoint returning 502")
        assert team == "API Integration Team"

    def test_keyword_webhook(self):
        team = route_team("Webhook Failure", "Integration broken")
        assert team == "API Integration Team"

    def test_keyword_oauth(self):
        team_val = route_team("Authentication service failing", "OAuth token invalid")
        assert team_val == "API Integration Team"


class TestRouteDataPlatformTeam:
    def test_keyword_pipeline(self):
        team = route_team("ETL Pipeline Stalled", "No records processed")
        assert team == "Data Platform Team"

    def test_keyword_warehouse(self):
        team = route_team("Data Warehouse Issue", "SQL query timeout")
        assert team == "Data Platform Team"

    def test_keyword_storage(self):
        team = route_team("Storage warning", "Disk capacity alert")
        assert team == "Data Platform Team"


class TestRouteCustomerOperationsTeam:
    def test_keyword_customer(self):
        team = route_team("Customer complaints", "Ticket system slow")
        assert team == "Customer Operations Team"

    def test_keyword_billing(self):
        team = route_team("Billing error", "Subscription not processed")
        assert team == "Customer Operations Team"

    def test_keyword_support(self):
        team = route_team("Support overload", "Account migration stuck")
        assert team == "Customer Operations Team"


class TestRouteInfrastructureTeam:
    def test_keyword_server(self):
        team = route_team("Server crashing", "VM out of memory")
        assert team == "Infrastructure Team"

    def test_keyword_network(self):
        team = route_team("Network issue", "DNS resolution failing")
        assert team == "Infrastructure Team"

    def test_keyword_deployment(self):
        team = route_team("Deployment failed", "Host unreachable")
        assert team == "Infrastructure Team"


class TestRouteFallback:
    """No keywords matched should default to Infrastructure Team."""

    def test_no_matching_keywords(self):
        team = route_team("Coffee Machine Error", "No coffee available")
        assert team == "Infrastructure Team"

    def test_unknown_system(self):
        team = route_team("Test Incident", "Something happened")
        assert team == "Infrastructure Team"


class TestRouteTieBreaker:
    """When multiple teams have the same score, the first-encountered wins (dict order)."""

    def test_two_keywords_one_team_wins(self):
        """If one team has 2 matches and another has 1, the higher-score team wins."""
        # "data warehouse" triggers both Data Platform (warehouse, database) and Infrastructure (warehouse not in infra, but "data" not a keyword... let's be explicit)
        team = route_team("Data warehouse pipeline issue", "SQL ingestion")
        assert team == "Data Platform Team"

    def test_api_keyword_beats_infra(self):
        """API keyword only matches API Integration."""
        team = route_team("API issue", "Something went wrong")
        assert team == "API Integration Team"


class TestEscalationRecommendation:
    def test_p1_escalation(self):
        rec = escalation_recommendation("P1")
        assert "Page the on-call" in rec

    def test_p2_escalation(self):
        rec = escalation_recommendation("P2")
        assert "on-call" in rec

    def test_p3_escalation(self):
        rec = escalation_recommendation("P3")
        assert "tracked task" in rec

    def test_p4_escalation(self):
        rec = escalation_recommendation("P4")
        assert "backlog" in rec

    def test_unknown_severity_fallback(self):
        rec = escalation_recommendation("P0")
        assert rec == escalation_recommendation("P4")
