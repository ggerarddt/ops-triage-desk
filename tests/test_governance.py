"""Tests for P1 approval gate and persisted audit record creation.

Verifies:
- Operator P1 submissions are stored as pending.
- Supervisor P1 submissions are stored as approved.
- Non-P1 incidents have no approval requirement.
- Audit log records are created on submission.
- Role-based admin access still honoured.
"""
import json

import pytest
from core.config import SEED_USERS
from core.database import init_schema, seed_users, list_incidents, list_audit_log, save_audit_log
from app import app


@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("triage") / "test.db"
    init_schema(str(db_file))
    seed_users(SEED_USERS, str(db_file))
    return str(db_file)


@pytest.fixture(autouse=True)
def patch_db(monkeypatch, test_db_path):
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


class TestP1OperatorPending:
    """Operator P1 submissions should be stored as pending."""

    def test_operator_p1_pending(self, client):
        """Operator submits P1 incident — should be pending."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/api/triage", data=json.dumps({
            "title": "Database Down - P1",
            "description": "All queries failing",
            "business_area": "Postal Service",
            "system_affected": "Analytics DB",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        }), content_type="application/json")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["severity"] == "P1"
        assert body["status"] == "pending"
        assert body["requires_approval"] is True

    def test_operator_p1_stored_in_db(self, client):
        """Operator P1 should be persisted in SQLite with pending status."""
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        client.post("/api/triage", data=json.dumps({
            "title": "Operator P1 Test",
            "description": "Test description",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        }), content_type="application/json")
        incidents = list_incidents()
        assert len(incidents) >= 1
        last = incidents[0]
        assert last["status"] == "pending"
        assert last["severity_level"] == 1


class TestP1SupervisorApproved:
    """Supervisor P1 submissions should be stored as approved."""

    def test_supervisor_p1_approved(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/api/triage", data=json.dumps({
            "title": "Supervisor P1",
            "description": "Critical outage",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        }), content_type="application/json")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["severity"] == "P1"
        assert body["status"] == "approved"
        assert body["requires_approval"] is False


class TestNonP1NoApproval:
    """Non-P1 incidents should always be approved."""

    def test_p2_operator_approved(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        # P2: medium impact, high urgency, no customer
        resp = client.post("/api/triage", data=json.dumps({
            "title": "P2 Test",
            "description": "Something broke",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "medium",
            "urgency": "high",
            "customer_impact": "no",
        }), content_type="application/json")
        body = resp.get_json()
        assert body["severity"] == "P2"
        assert body["status"] == "approved"
        assert body["requires_approval"] is False

    def test_p4_operator_approved(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/api/triage", data=json.dumps({
            "title": "P4 Test",
            "description": "Minor issue",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "low",
            "urgency": "low",
            "customer_impact": "no",
        }), content_type="application/json")
        body = resp.get_json()
        assert body["status"] == "approved"
        assert body["requires_approval"] is False


class TestAuditRecordCreation:
    """Audit records should be created on every submission."""

    def test_audit_record_on_submission(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/api/triage", data=json.dumps({
            "title": "Audit Test",
            "description": "Creates audit record",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        }), content_type="application/json")
        assert resp.status_code == 200

        audit_entries = list_audit_log()
        submitted = [e for e in audit_entries if e["action"] == "submitted"]
        assert len(submitted) >= 1
        assert submitted[0]["username"] == "operator1"
        assert submitted[0]["role"] == "operator"
        assert submitted[0]["severity"] == "P1"

    def test_audit_has_all_fields(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        client.post("/api/triage", data=json.dumps({
            "title": "Full Audit",
            "description": "Verify fields",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "medium",
            "urgency": "medium",
            "customer_impact": "no",
        }), content_type="application/json")

        audit_entries = list_audit_log()
        assert len(audit_entries) >= 1
        entry = audit_entries[0]
        # All required fields should be present
        assert entry["username"]
        assert entry["role"]
        assert entry["action"]
        assert entry["timestamp"]


class TestRoleBasedAdminAccess:
    """Admin route should remain role-gated."""

    def test_operator_cannot_access_admin(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin")
        assert resp.status_code == 302  # Redirect

    def test_supervisor_can_access_admin(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin")
        assert resp.status_code == 200


class TestResultPageApproval:
    """Result page should indicate pending approval for operator P1s."""

    def test_result_page_with_pending_approval(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/triage/submit", data={
            "title": "P1 Pending Test",
            "description": "Requires approval",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        })
        html = resp.data.decode()
        assert "PENDING" in html
        assert "Approval" in html
        assert "supervisor" in html.lower()

    def test_result_page_with_approved_p1(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        resp = client.post("/triage/submit", data={
            "title": "P1 Approved Test",
            "description": "Supervisor submitted",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        })
        html = resp.data.decode()
        assert "APPROVED" in html
        # Should NOT show the pending approval warning
        assert "Pending Approval" not in html
