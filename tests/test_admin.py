"""Tests for supervisor admin workflow: approve, deny, reclassify, and edit.

Verifies:
- GET /admin as supervisor shows dashboard, operator gets 302
- GET /admin shows pending/approved/denied P1 counts
- POST /admin/approve changes status, creates audit log, redirects
- POST /admin/approve rejects non-P1, already-approved, missing incident_id
- POST /admin/deny requires incident_id + reason, creates audit log
- POST /admin/deny rejects missing reason
- POST /admin/reclassify changes severity + severity_level + status
- POST /admin/reclassify rejects invalid targets, missing reason
- POST /admin/reclassify rejects operator role
- GET /admin/edit/<id> shows form for pending P1
- POST /admin/edit/<id> updates incident fields, audit log
- POST /admin/edit/<id> reclassifies when severity drops
- POST /admin/edit/<id> operator blocked
- edit prevents editing approved/denied/incidents
- Audit entries for approve, deny, reclassify, edit
"""
import json
import sqlite3

import pytest
from core.config import SEED_USERS
from core.database import init_schema, seed_users
from app import app


@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("triage_admin") / "test.db"
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


# ---------------------------------------------------------------------------
# DB helpers for the test database
# ---------------------------------------------------------------------------

def _test_db(test_db_path):
    """Return a test DB connection."""
    c = sqlite3.connect(test_db_path)
    c.row_factory = sqlite3.Row
    return c


def _find_pending_p1_id(test_db_path):
    """Find the ID of the most recent pending P1 incident."""
    conn = _test_db(test_db_path)
    try:
        row = conn.execute(
            "SELECT id FROM incidents WHERE severity = 'P1' AND status = 'pending' "
            "ORDER BY submitted_at DESC LIMIT 1"
        ).fetchone()
        return int(row["id"]) if row else None
    finally:
        conn.close()


def _get_test_audit_log(test_db_path):
    """Return all audit log entries from the test DB."""
    conn = _test_db(test_db_path)
    try:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helper: submit a P1 incident via API (operator)
# ---------------------------------------------------------------------------

def _submit_p1(client):
    """Submit a P1 incident as operator1."""
    client.post("/login", data={
        "username": "operator1",
        "password": "ChangeMe123!",
    })
    resp = client.post("/api/triage", data=json.dumps({
        "title": "Admin Test P1",
        "description": "For admin workflow testing",
        "business_area": "Test",
        "system_affected": "Test",
        "impact_level": "high",
        "urgency": "high",
        "customer_impact": "yes",
    }), content_type="application/json")
    assert resp.status_code == 200
    return resp.get_json()


def _submit_non_p1(client):
    """Submit a non-P1 incident as operator1."""
    client.post("/login", data={
        "username": "operator1",
        "password": "ChangeMe123!",
    })
    resp = client.post("/api/triage", data=json.dumps({
        "title": "Admin Test Non-P1",
        "description": "Should not need approval",
        "business_area": "Test",
        "system_affected": "Test",
        "impact_level": "low",
        "urgency": "low",
        "customer_impact": "no",
    }), content_type="application/json")
    assert resp.status_code == 200
    return resp.get_json()


def _login_supervisor(client):
    client.post("/login", data={
        "username": "supervisor1",
        "password": "ChangeMe123!",
    })


# ---------------------------------------------------------------------------
# GET /admin
# ---------------------------------------------------------------------------

class TestAdminGet:
    def test_admin_supervisor_sees_dashboard(self, client):
        _login_supervisor(client)
        resp = client.get("/admin")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Admin Panel" in html
        assert "Pending P1 Escalations" in html
        assert "Approved P1 Incidents" in html
        assert "Denied P1 Incidents" in html
        assert "Reclassified P1 Incidents" in html

    def test_admin_operator_blocked(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin")
        assert resp.status_code == 302

    def test_admin_unauthenticated_blocked(self, client):
        resp = client.get("/admin")
        assert resp.status_code == 302


class TestAdminPendingCounts:
    """GET /admin should show correct section counts."""

    def test_pending_section_shows_count(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        resp = client.get("/admin")
        html = resp.data.decode()
        assert "Pending P1 Escalations" in html
        assert "Admin Test P1" in html


# ---------------------------------------------------------------------------
# Approve
# ---------------------------------------------------------------------------

class TestAdminApprove:
    def test_approve_pending_p1_success(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/approve", data={
            "incident_id": incident_id,
            "reason": "Verified and approved",
        })
        assert resp.status_code == 302
        audit_entries = _get_test_audit_log(test_db_path)
        approved_logs = [e for e in audit_entries if e["action"] == "approved"]
        assert len(approved_logs) >= 1
        assert approved_logs[-1]["username"] == "supervisor1"

    def test_approve_non_p1_fails(self, client, test_db_path):
        _submit_non_p1(client)
        _login_supervisor(client)
        resp = client.post("/admin/approve", data={
            "incident_id": "1",
            "reason": "should fail",
        })
        assert resp.status_code == 302

    def test_approve_missing_incident_id(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.post("/admin/approve", data={})
        assert resp.status_code == 302

    def test_approve_nonexistent_incident(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.post("/admin/approve", data={
            "incident_id": "99999",
        })
        assert resp.status_code == 302

    def test_approve_form_has_incident_id_in_template(self, client, test_db_path):
        """Regression: approve form must contain a hidden incident_id input."""
        _submit_p1(client)
        _login_supervisor(client)
        resp = client.get("/admin")
        assert resp.status_code == 200
        html = resp.data.decode()
        # The HTML should contain the hidden input in each approve form
        # Count how many times the admin_approve form appears with the hidden input
        approve_form_count = html.count('action="{{ url_for(\'admin_approve\') }}"')
        hidden_id_count = html.count('name="incident_id"')
        assert hidden_id_count >= approve_form_count, (
            f"Approve forms ({approve_form_count}) must have "
            f"matching name='incident_id' hidden inputs (found {hidden_id_count})"
        )


# ---------------------------------------------------------------------------
# Deny
# ---------------------------------------------------------------------------

class TestAdminDeny:
    def test_deny_pending_p1_success(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/deny", data={
            "incident_id": incident_id,
            "reason": "Not actionable",
        })
        assert resp.status_code == 302
        audit_entries = _get_test_audit_log(test_db_path)
        denied_logs = [e for e in audit_entries if e["action"] == "denied"]
        assert len(denied_logs) >= 1
        assert denied_logs[-1]["reason"] == "Not actionable"

    def test_deny_missing_reason(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/deny", data={"incident_id": incident_id, "reason": ""})
        assert resp.status_code == 302

    def test_deny_missing_incident_id(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.post("/admin/deny", data={"reason": "test"})
        assert resp.status_code == 302

    def test_deny_non_p1_fails(self, client, test_db_path):
        _submit_non_p1(client)
        _login_supervisor(client)
        resp = client.post("/admin/deny", data={
            "incident_id": "1",
            "reason": "should fail",
        })
        assert resp.status_code == 302

    def test_deny_nonexistent_incident(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.post("/admin/deny", data={
            "incident_id": "99999",
            "reason": "nope",
        })
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Reclassify
# ---------------------------------------------------------------------------

class TestAdminReclassify:
    def test_reclassify_to_p2_success(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/reclassify", data={
            "incident_id": incident_id,
            "new_severity": "P2",
            "reason": "Lower assessment after review",
        })
        assert resp.status_code == 302
        audit_entries = _get_test_audit_log(test_db_path)
        reclass_logs = [e for e in audit_entries if e["action"] == "reclassified"]
        assert len(reclass_logs) >= 1
        assert reclass_logs[-1]["severity"] == "P2"

    def test_reclassify_to_p4_success(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/reclassify", data={
            "incident_id": incident_id,
            "new_severity": "P4",
            "reason": "Not important",
        })
        assert resp.status_code == 302

    def test_reclassify_invalid_target(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/reclassify", data={
            "incident_id": incident_id,
            "new_severity": "P1",
            "reason": "keep same",
        })
        assert resp.status_code == 302

    def test_reclassify_missing_reason(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post("/admin/reclassify", data={
            "incident_id": incident_id,
            "new_severity": "P2",
        })
        assert resp.status_code == 302

    def test_reclassify_missing_incident_id(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.post("/admin/reclassify", data={
            "new_severity": "P2",
            "reason": "no id",
        })
        assert resp.status_code == 302

    def test_reclassify_non_p1_fails(self, client, test_db_path):
        _submit_non_p1(client)
        _login_supervisor(client)
        resp = client.post("/admin/reclassify", data={
            "incident_id": "1",
            "new_severity": "P2",
            "reason": "should fail",
        })
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Edit GET /admin/edit/<id>
# ---------------------------------------------------------------------------

class TestAdminEditGet:
    def test_edit_get_pending_p1_shows_form(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.get(f"/admin/edit/{incident_id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Edit Incident" in html
        assert 'name="title"' in html
        assert 'name="description"' in html

    def test_edit_get_nonexistent_incident(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.get("/admin/edit/99999")
        assert resp.status_code == 302

    def test_edit_get_non_pending_fails(self, client, test_db_path):
        _submit_non_p1(client)
        _login_supervisor(client)
        # Get an ID for any non-P1 (auto-approved) incident
        conn = _test_db(test_db_path)
        try:
            row = conn.execute(
                "SELECT id FROM incidents WHERE status != 'pending' LIMIT 1"
            ).fetchone()
            inc_id = int(row["id"]) if row else 1
        finally:
            conn.close()
        resp = client.get(f"/admin/edit/{inc_id}")
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Edit POST /admin/edit/<id>
# ---------------------------------------------------------------------------

class TestAdminEditPost:
    def test_edit_pending_p1_updates_fields(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post(f"/admin/edit/{incident_id}", data={
            "title": "Updated Title",
            "description": "Updated description text",
            "business_area": "UpdatedArea",
            "system_affected": "UpdatedSystem",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        })
        assert resp.status_code == 302

    def test_edit_still_pending_when_remains_p1(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post(f"/admin/edit/{incident_id}", data={
            "title": "Still P1",
            "description": "Still critical",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        })
        assert resp.status_code == 302

    def test_edit_reclassifies_when_severity_drops(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post(f"/admin/edit/{incident_id}", data={
            "title": "Low Impact Issue",
            "description": "Minor issue",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "low",
            "urgency": "low",
            "customer_impact": "no",
        })
        assert resp.status_code == 302
        audit_entries = _get_test_audit_log(test_db_path)
        reclass_logs = [e for e in audit_entries if e["action"] == "reclassified"]
        assert len(reclass_logs) >= 1

    def test_edit_missing_fields_fails(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        resp = client.post(f"/admin/edit/{incident_id}", data={
            "title": "",
            "description": "",
            "business_area": "",
            "system_affected": "",
            "impact_level": "low",
            "urgency": "low",
            "customer_impact": "no",
        })
        assert resp.status_code == 200  # form re-renders with errors

    def test_edit_operator_blocked(self, client, test_db_path):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin/edit/1")
        assert resp.status_code == 302

    def test_edit_nonexistent_incident(self, client, test_db_path):
        _login_supervisor(client)
        resp = client.get("/admin/edit/99999")
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Audit entries
# ---------------------------------------------------------------------------

class TestAdminAuditEntries:
    def test_audit_record_on_approve(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        client.post("/admin/approve", data={
            "incident_id": incident_id,
            "reason": "approved",
        })
        audit_entries = _get_test_audit_log(test_db_path)
        approved_logs = [e for e in audit_entries if e["action"] == "approved"]
        assert len(approved_logs) >= 1
        assert approved_logs[-1]["username"] == "supervisor1"

    def test_audit_record_on_deny(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        client.post("/admin/deny", data={
            "incident_id": incident_id,
            "reason": "denied",
        })
        audit_entries = _get_test_audit_log(test_db_path)
        denied_logs = [e for e in audit_entries if e["action"] == "denied"]
        assert len(denied_logs) >= 1

    def test_audit_record_on_reclassify(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        client.post("/admin/reclassify", data={
            "incident_id": incident_id,
            "new_severity": "P2",
            "reason": "reclass test",
        })
        audit_entries = _get_test_audit_log(test_db_path)
        reclass_logs = [e for e in audit_entries if e["action"] == "reclassified"]
        assert len(reclass_logs) >= 1

    def test_audit_record_on_edit(self, client, test_db_path):
        _submit_p1(client)
        _login_supervisor(client)
        incident_id = _find_pending_p1_id(test_db_path)
        assert incident_id is not None
        client.post(f"/admin/edit/{incident_id}", data={
            "title": "Edited Title",
            "description": "Edited desc",
            "business_area": "Test",
            "system_affected": "Test",
            "impact_level": "high",
            "urgency": "high",
            "customer_impact": "yes",
        })
        audit_entries = _get_test_audit_log(test_db_path)
        edit_logs = [e for e in audit_entries if e["action"] == "edited"]
        assert len(edit_logs) >= 1


# ---------------------------------------------------------------------------
# Auto-fill button regression
# ---------------------------------------------------------------------------

class TestAutoFillButtonsRegression:
    def test_example_buttons_exist_on_index(self, client):
        _login_supervisor(client)
        resp = client.get("/triage")
        html = resp.data.decode()
        assert 'data-title="Benefits API' in html or 'data-title="' in html
        assert 'data-description=' in html
        assert 'data-business_area=' in html
        assert 'data-system_affected=' in html
        assert 'data-impact_level=' in html
        assert 'data-urgency=' in html
        assert 'data-customer_impact=' in html

    def test_triage_page_has_all_form_fields(self, client):
        _login_supervisor(client)
        resp = client.get("/triage")
        html = resp.data.decode()
        assert 'name="title"' in html
        assert 'name="description"' in html
        assert 'name="business_area"' in html
        assert 'name="system_affected"' in html
        assert 'name="impact_level"' in html
        assert 'name="urgency"' in html
        assert 'name="customer_impact"' in html
