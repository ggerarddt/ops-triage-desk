"""Route definitions for the triage application.

Handles HTTP concerns -- parsing, rendering, session management.
Business logic is delegated to services/ which remain framework-independent.
Governance features: input validation, P1 approval gate, audit logging, PII redaction.
"""
from __future__ import annotations

import json
import logging
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from core.database import (
    seed_users,
    session as db_session,
    list_incidents,
    save_audit_log,
    list_audit_log,
    save_incident,
    severity_to_level,
    get_by_id,
    get_pending_p1s,
    get_all_filtered_by,
    approve as db_approve,
    deny as db_deny,
    reclassify as db_reclassify,
    update_pending as db_update_pending,
)
from core.config import SEED_USERS
from core.gov_config import P1_APPROVAL_ENABLED, ALLOWED_RECLASSIFY_TARGETS
from core.redactor import redact
from services.auth_service import find_user_by_username, verify_password
from services.severity_service import classify_severity
from services.triage_service import run_triage
from services.validation import validate_incident_input, ValidationError

logger = logging.getLogger("ops-triage")


# ---------------------------------------------------------------------------
# Session hook (before every request)
# ---------------------------------------------------------------------------

def setup_before_request(app: Flask) -> None:
    """Attach current user to `g` on every request."""

    @app.before_request
    def _load_user() -> None:
        if "user_id" not in session:
            g.user = None
            return
        with db_session() as conn:
            row = conn.execute(
                "SELECT id, username, role FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        g.user = dict(row) if row else None


# ---------------------------------------------------------------------------
# Decorator shims
# ---------------------------------------------------------------------------

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("triage"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

def _register_auth_routes(router: Flask) -> None:
    """Register login, logout, and root redirect."""

    @router.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("triage"))
        return redirect(url_for("login"))

    @router.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = find_user_by_username(username)
            if user and verify_password(user, password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for("triage"))
            flash("Invalid username or password.", "danger")
        return render_template("login.html")

    @router.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Triage routes
# ---------------------------------------------------------------------------

def _register_triage_routes(router: Flask) -> None:
    """Register the triage form and submission handlers (web + JSON API)."""

    @router.route("/triage")
    @login_required
    def triage():
        return render_template("index.html", user_role=session.get("role"))

    @router.route("/triage/submit", methods=["POST"])
    @login_required
    def triage_submit():
        form = request.form
        errors = validate_incident_input(
            form.get("title", ""),
            form.get("description", ""),
            form.get("business_area", ""),
            form.get("system_affected", ""),
            form.get("impact_level", ""),
            form.get("urgency", ""),
            form.get("customer_impact", ""),
        )
        if errors:
            for err in errors:
                flash(f"{err.field}: {err.message}", "danger")
            return redirect(url_for("triage"))

        # Determine approval status before calling run_triage so the DB
        # save reflects the correct value.
        severity, _ = classify_severity(
            form["impact_level"], form["urgency"], form["customer_impact"],
        )
        if severity == "P1" and session.get("role") != "supervisor" and P1_APPROVAL_ENABLED:
            approval_status = "pending"
        else:
            approval_status = "approved"

        result = run_triage(
            title=form["title"],
            description=form["description"],
            business_area=form["business_area"],
            system_affected=form["system_affected"],
            impact_level=form["impact_level"],
            urgency=form["urgency"],
            customer_impact=form["customer_impact"],
            submitted_by=session["username"],
            approval_status=approval_status,
        )

        result["requires_approval"] = approval_status == "pending"
        result["submitted_by_role"] = session.get("role")

        # Record audit log (description redacted)
        save_audit_log({
            "username": session["username"],
            "role": session.get("role"),
            "incident_id": None,  # ID not yet assigned (handled by triage_service)
            "severity": result["severity"],
            "team": result["suggested_team"],
            "action": "submitted",
            "reason": result["status"],
        })

        redacted_desc = redact(result["description"])[:100]
        logger.info(
            "Triage: sev=%s team=%s status=%s desc_len=%d",
            result["severity"],
            result["suggested_team"],
            result["status"],
            len(redacted_desc),
        )
        return render_template("result.html", result=result)

    @router.route("/api/triage", methods=["POST"])
    @login_required
    def api_triage():
        """JSON API: accept incident data and return classification."""
        data = request.get_json(silent=True)
        if not data:
            return {"error": "Invalid or missing JSON body"}, 400

        errors = validate_incident_input(
            data.get("title", ""),
            data.get("description", ""),
            data.get("business_area", ""),
            data.get("system_affected", ""),
            data.get("impact_level", ""),
            data.get("urgency", ""),
            data.get("customer_impact", ""),
        )
        if errors:
            error_items = [{"field": e.field, "message": e.message} for e in errors]
            return {"error": "Validation failed", "details": error_items}, 400

        # Determine approval status before calling run_triage so the DB
        # save reflects the correct value.
        severity, _ = classify_severity(
            data["impact_level"], data["urgency"], data["customer_impact"],
        )
        if severity == "P1" and session.get("role") != "supervisor" and P1_APPROVAL_ENABLED:
            approval_status = "pending"
        else:
            approval_status = "approved"

        result = run_triage(
            title=data["title"],
            description=data["description"],
            business_area=data["business_area"],
            system_affected=data["system_affected"],
            impact_level=data["impact_level"],
            urgency=data["urgency"],
            customer_impact=data["customer_impact"],
            submitted_by=session["username"],
            approval_status=approval_status,
        )

        result["requires_approval"] = approval_status == "pending"
        result["submitted_by_role"] = session.get("role")


        # Record audit log
        save_audit_log({
            "username": session["username"],
            "role": session.get("role"),
            "incident_id": None,
            "severity": result["severity"],
            "team": result["suggested_team"],
            "action": "submitted",
            "reason": result["status"],
        })
        logger.info(
            "Triage (API): sev=%s team=%s status=%s",
            result["severity"],
            result["suggested_team"],
            result["status"],
        )

        response_data = {
            "incident": {
                "title": result["title"],
                "description": result["description"],
                "business_area": result["business_area"],
                "system_affected": result["system_affected"],
                "impact_level": result["impact_level"],
                "urgency": result["urgency"],
                "customer_impact": result["customer_impact"],
            },
            "severity": result["severity"],
            "severity_description": result["severity_description"],
            "suggested_team": result["suggested_team"],
            "escalation_recommendation": result["escalation_recommendation"],
            "handoff_summary": result["handoff_summary"],
            "mock_payload": result["mock_payload"],
            "status": result["status"],
            "requires_approval": result["requires_approval"],
        }
        return json.dumps(response_data), 200, {"Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Audit route
# ---------------------------------------------------------------------------

def _register_audit_routes(router: Flask) -> None:
    """Register the audit log view."""

    @router.route("/audit")
    @login_required
    def audit():
        incidents = list_incidents()
        audit_entries = list_audit_log()
        return render_template("audit.html", incidents=incidents, audit_entries=audit_entries)


# ---------------------------------------------------------------------------
# Admin route
# ---------------------------------------------------------------------------

def _register_admin_routes(router: Flask) -> None:
    """Register the supervisor-only admin dashboard with approve, deny,
    reclassification, and edit capabilities."""
    from services.triage_service import _run_triage_pipeline

    def _get_form_or_json():
        data = request.get_json(silent=True)
        if data:
            return data
        return request.form

    @router.route("/admin")
    @role_required("supervisor")
    def admin():
        pending_p1s = get_pending_p1s()
        approved_p1s = get_all_filtered_by(severity="P1", status="approved")
        denied_p1s = get_all_filtered_by(severity="P1", status="denied")
        reclassified_p1s = get_all_filtered_by(severity="P1", status="reclassified")
        return render_template(
            "admin.html",
            pending_p1s=list(pending_p1s),
            approved_p1s=list(approved_p1s),
            denied_p1s=list(denied_p1s),
            reclassified_p1s=list(reclassified_p1s),
            edit_incident=None,
        )

    @router.route("/admin/approve", methods=["POST"])
    @role_required("supervisor")
    def admin_approve():
        data = _get_form_or_json()
        incident_id = int(data.get("incident_id", 0))
        if not incident_id:
            flash("incident_id is required.", "danger")
            return redirect(url_for("admin"))
        incident = get_by_id(incident_id)
        if not incident:
            flash("Incident not found.", "danger")
            return redirect(url_for("admin"))
        if incident["severity"] != "P1" or incident["status"] != "pending":
            flash("Only pending P1 incidents can be approved.", "warning")
            return redirect(url_for("admin"))
        db_approve(incident_id, data.get("reason"))
        save_audit_log({
            "username": session.get("username", "system"),
            "role": "supervisor",
            "incident_id": incident_id,
            "severity": "P1",
            "team": incident.get("suggested_team"),
            "action": "approved",
            "reason": data.get("reason"),
        })
        flash(f"Incident {incident_id} approved.", "success")
        return redirect(url_for("admin"))

    @router.route("/admin/deny", methods=["POST"])
    @role_required("supervisor")
    def admin_deny():
        data = _get_form_or_json()
        incident_id = int(data.get("incident_id", 0))
        reason = data.get("reason", "").strip()
        if not incident_id:
            flash("incident_id is required.", "danger")
            return redirect(url_for("admin"))
        if not reason:
            flash("Denial reason is required.", "danger")
            return redirect(url_for("admin"))
        incident = get_by_id(incident_id)
        if not incident:
            flash("Incident not found.", "danger")
            return redirect(url_for("admin"))
        if incident["severity"] != "P1" or incident["status"] != "pending":
            flash("Only pending P1 incidents can be denied.", "warning")
            return redirect(url_for("admin"))
        db_deny(incident_id, reason)
        save_audit_log({
            "username": session.get("username", "system"),
            "role": "supervisor",
            "incident_id": incident_id,
            "severity": "P1",
            "team": incident.get("suggested_team"),
            "action": "denied",
            "reason": reason,
        })
        flash(f"Incident {incident_id} denied.", "success")
        return redirect(url_for("admin"))

    @router.route("/admin/reclassify", methods=["POST"])
    @role_required("supervisor")
    def admin_reclassify():
        data = _get_form_or_json()
        incident_id = int(data.get("incident_id", 0))
        new_severity = data.get("new_severity", "").strip()
        reason = data.get("reason", "").strip()
        if not incident_id:
            flash("incident_id is required.", "danger")
            return redirect(url_for("admin"))
        if not reason:
            flash("Reclassification reason is required.", "danger")
            return redirect(url_for("admin"))
        if new_severity not in ALLOWED_RECLASSIFY_TARGETS:
            flash(
                f"Invalid reclassification target. Must be one of: {', '.join(ALLOWED_RECLASSIFY_TARGETS)}.",
                "danger",
            )
            return redirect(url_for("admin"))
        incident = get_by_id(incident_id)
        if not incident:
            flash("Incident not found.", "danger")
            return redirect(url_for("admin"))
        if incident["severity"] != "P1" or incident["status"] != "pending":
            flash("Only pending P1 incidents can be reclassified.", "warning")
            return redirect(url_for("admin"))
        db_reclassify(incident_id, new_severity)
        save_audit_log({
            "username": session.get("username", "system"),
            "role": "supervisor",
            "incident_id": incident_id,
            "severity": new_severity,
            "team": incident.get("suggested_team"),
            "action": "reclassified",
            "reason": reason,
        })
        flash(f"Incident {incident_id} reclassified to {new_severity}.", "success")
        return redirect(url_for("admin"))

    @router.route("/admin/edit/<int:incident_id>", methods=["GET"])
    @role_required("supervisor")
    def admin_edit_get(incident_id):
        incident = get_by_id(incident_id)
        if not incident:
            flash("Incident not found.", "danger")
            return redirect(url_for("admin"))
        if incident["status"] != "pending" or incident["severity"] != "P1":
            flash("Only pending P1 incidents can be edited in admin.", "warning")
            return redirect(url_for("admin"))
        return render_template(
            "admin.html",
            pending_p1s=list(get_pending_p1s()),
            approved_p1s=list(get_all_filtered_by(severity="P1", status="approved")),
            denied_p1s=list(get_all_filtered_by(severity="P1", status="denied")),
            reclassified_p1s=list(get_all_filtered_by(severity="P1", status="reclassified")),
            edit_incident=dict(incident),
        )

    @router.route("/admin/edit/<int:incident_id>", methods=["POST"])
    @role_required("supervisor")
    def admin_edit_post(incident_id):
        form = request.form
        errors = validate_incident_input(
            form.get("title", ""),
            form.get("description", ""),
            form.get("business_area", ""),
            form.get("system_affected", ""),
            form.get("impact_level", ""),
            form.get("urgency", ""),
            form.get("customer_impact", ""),
        )
        if errors:
            for err in errors:
                flash(f"{err.field}: {err.message}", "danger")
            incident = get_by_id(incident_id)
            return render_template(
                "admin.html",
                pending_p1s=list(get_pending_p1s()),
                approved_p1s=list(get_all_filtered_by(severity="P1", status="approved")),
                denied_p1s=list(get_all_filtered_by(severity="P1", status="denied")),
                reclassified_p1s=list(get_all_filtered_by(severity="P1", status="reclassified")),
                edit_incident=dict(incident) if incident else None,
            )
        incident = get_by_id(incident_id)
        if not incident:
            flash("Incident not found.", "danger")
            return redirect(url_for("admin"))
        if incident["status"] != "pending":
            flash("Only pending incidents can be edited.", "warning")
            return redirect(url_for("admin"))
        db_update_pending(
            incident_id,
            form["title"],
            form["description"],
            form["business_area"],
            form["system_affected"],
            form["impact_level"],
            form["urgency"],
            form["customer_impact"],
        )
        new_severity, new_sev_desc = classify_severity(
            form["impact_level"], form["urgency"], form["customer_impact"],
        )
        new_team = __import__("services.routing_service", fromlist=["route_team"]).route_team(
            form["title"], form["description"],
        )
        new_escalation = __import__("services.routing_service", fromlist=["escalation_recommendation"]).escalation_recommendation(new_severity)
        new_handoff = __import__("core.summary_service", fromlist=["build_handoff_summary"]).build_handoff_summary(
            form["title"], form["business_area"], form["system_affected"],
            form["impact_level"], form["urgency"], form["customer_impact"],
            new_severity, new_sev_desc, new_team,
        )
        new_sev_level = severity_to_level(new_severity)
        with db_session() as conn:
            conn.execute(
                "UPDATE incidents SET severity = ?, severity_description = ?, suggested_team = ?, escalation_recommendation = ?, handoff_summary = ?, severity_level = ? WHERE id = ?",
                (new_severity, new_sev_desc, new_team, new_escalation, new_handoff, new_sev_level, incident_id),
            )
        action = "reclassified" if (new_severity != "P1" and incident["severity"] == "P1") else "edited"
        save_audit_log({
            "username": session.get("username", "system"),
            "role": session.get("role"),
            "incident_id": incident_id,
            "severity": new_severity,
            "team": new_team,
            "action": action,
            "reason": f"Edited by supervisor. Result: {new_severity} -> {new_team}",
        })
        flash(f"Incident {incident_id} updated. New severity: {new_severity}.", "success")
        return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def register_routes(router: Flask) -> None:
    """Attach all routes and the before-request hook to the Flask app."""
    setup_before_request(router)
    _register_auth_routes(router)
    _register_triage_routes(router)
    _register_audit_routes(router)
    _register_admin_routes(router)
