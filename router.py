"""Route definitions for the triage application.

This module is framework-agnostic in spirit — the Flask-specific bits
(render template, redirect, session) only exist inside the handlers.
The session-loading hook is registered via `register_hooks`.
"""
from __future__ import annotations

import json
import logging

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

from core.database import seed_users, session as db_session
from core.config import SEED_USERS
from services.auth_service import find_user_by_username, verify_password
from services.triage_service import run_triage
from services import auth_service

logger = logging.getLogger("ops-triage")


# ---------------------------------------------------------------------------
# Session hook (before every request)
# ---------------------------------------------------------------------------

def setup_before_request(app: Flask) -> None:
    """Attach current user to `g` on every request."""

    @app.before_request
    def _load_user() -> None:  # type: ignore[misc]
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

from functools import wraps

def login_required(view_func):  # type: ignore[misc]
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(*roles):  # type: ignore[misc]
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
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
        return render_template("index.html")

    @router.route("/triage/submit", methods=["POST"])
    @login_required
    def triage_submit():
        form = request.form
        required = ["title", "description", "business_area", "system_affected",
                    "impact_level", "urgency", "customer_impact"]
        if not all(form.get(f) for f in required):
            flash("All fields are required.", "danger")
            return redirect(url_for("triage"))

        result = run_triage(
            title=form["title"],
            description=form["description"],
            business_area=form["business_area"],
            system_affected=form["system_affected"],
            impact_level=form["impact_level"],
            urgency=form["urgency"],
            customer_impact=form["customer_impact"],
            submitted_by=session["username"],
        )

        logger.info("Triage complete: severity=%s team=%s", result["severity"], result["suggested_team"])
        return render_template("result.html", result=result)

    @router.route("/api/triage", methods=["POST"])
    @login_required
    def api_triage():
        """JSON API: accept incident data and return classification."""
        data = request.get_json(silent=True)
        if not data:
            return {"error": "Invalid or missing JSON body"}, 400

        required = ["title", "description", "business_area", "system_affected",
                    "impact_level", "urgency", "customer_impact"]
        if not all(data.get(f) for f in required):
            return {"error": f"Missing required fields: {required}"}, 400

        result = run_triage(
            title=data["title"],
            description=data["description"],
            business_area=data["business_area"],
            system_affected=data["system_affected"],
            impact_level=data["impact_level"],
            urgency=data["urgency"],
            customer_impact=data["customer_impact"],
            submitted_by=session["username"],
        )

        logger.info("Triage complete (API): severity=%s team=%s", result["severity"], result["suggested_team"])

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
        }
        return json.dumps(response_data), 200, {"Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Audit route
# ---------------------------------------------------------------------------

def _register_audit_routes(router: Flask) -> None:
    """Register the audit log view."""
    from core.database import list_incidents

    @router.route("/audit")
    @login_required
    def audit():
        incidents = list_incidents()
        return render_template("audit.html", incidents=incidents)


# ---------------------------------------------------------------------------
# Admin route
# ---------------------------------------------------------------------------

def _register_admin_routes(router: Flask) -> None:
    """Register the supervisor-only admin placeholder."""

    @router.route("/admin")
    @role_required("supervisor")
    def admin():
        return render_template("admin.html")


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
