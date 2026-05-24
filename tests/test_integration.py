"""Integration tests for the full Flask application.

Covers route redirects, form submission, JSON API, and malformed input.
"""
import json

import pytest

from core.config import SEED_USERS
from core.database import init_schema, seed_users
from app import app


@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    """Create and seed a temporary database, return path."""
    db_file = tmp_path_factory.mktemp("triage") / "test.db"
    init_schema(str(db_file))
    seed_users(SEED_USERS, str(db_file))
    return str(db_file)


@pytest.fixture(autouse=True)
def patch_db(monkeypatch, test_db_path):
    """Ensure all db calls use the test database."""
    import core.database as db_mod

    orig_get = db_mod._get_conn

    def patched(path=None):
        return orig_get(test_db_path)

    monkeypatch.setattr(db_mod, "_get_conn", patched)
    return test_db_path


@pytest.fixture
def client(test_db_path):
    app.secret_key = "test-only"
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------

class TestAuthFlow:
    def test_root_redirects_to_login_when_unauthenticated(self, client):
        resp = client.get("/")
        assert resp.status_code == 302
        assert "login" in resp.location

    def test_login_redirects_to_triage(self, client):
        resp = client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "triage" in resp.location

    def test_audit_restricted_without_login(self, client):
        resp = client.get("/audit")
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Web form triage
# ---------------------------------------------------------------------------

class TestTriageForm:
    def test_post_triage_submit(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/triage/submit", data={
            "title": "API Gateway Error",
            "description": "502s on /api/v1/users",
            "business_area": "Public Admin",
            "system_affected": "API Gateway",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        }, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "P1" in html
        assert "API Integration Team" in html or "handoff" in html.lower()


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

class TestJsonApi:
    def test_api_triage_success(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        resp = client.post(
            "/api/triage",
            data=json.dumps({
                "title": "P1 - Database Down",
                "description": "Postgres not responding",
                "business_area": "Postal Service",
                "system_affected": "Analytics DB",
                "impact_level": "high",
                "urgency": "high",
                "customer_impact": "yes",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "application/json" in resp.content_type
        body = resp.get_json()
        assert body["incident"]["title"] == "P1 - Database Down"
        assert body["severity"] == "P1"
        assert body["suggested_team"] == "Data Platform Team"
        assert body["escalation_recommendation"]
        assert body["handoff_summary"]
        assert body["mock_payload"]

    def test_api_missing_body(self, client):
        """POST with no JSON body returns 400."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        # Send a POST with Content-Type but empty body
        resp = client.post(
            "/api/triage",
            data="",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_api_missing_fields(self, client):
        """POST with partial fields returns 400."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post(
            "/api/triage",
            data=json.dumps({"title": "Incomplete"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_api_response_mock_payload_valid_json(self, client):
        """Assert mock_payload in the response is itself valid serialisable JSON."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post(
            "/api/triage",
            data=json.dumps({
                "title": "Test",
                "description": "Test",
                "business_area": "Test",
                "system_affected": "Test",
                "impact_level": "low",
                "urgency": "low",
                "customer_impact": "no",
            }),
            content_type="application/json",
        )
        body = resp.get_json()
        # mock_payload should be a dict (serialisable to JSON)
        assert isinstance(body["mock_payload"], dict)
        json.dumps(body["mock_payload"])  # won't raise

    def test_api_unauthenticated(self, client):
        """Unauthenticated requests to /api/triage return 302 redirect."""
        resp = client.post(
            "/api/triage",
            data=json.dumps({
                "title": "Hacker",
                "description": "Hack",
                "business_area": "Hack",
                "system_affected": "Hack",
                "impact_level": "high",
                "urgency": "high",
                "customer_impact": "yes",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Malformed / edge-case inputs
# ---------------------------------------------------------------------------

class TestMalformedInput:
    def test_web_form_empty_fields(self, client):
        """Submitting an empty form should redirect back to triage, not 500."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/triage/submit", data={})
        assert resp.status_code == 302  # Redirect to triage

    def test_api_empty_json(self, client):
        """POST empty JSON object returns 400."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post(
            "/api/triage",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
