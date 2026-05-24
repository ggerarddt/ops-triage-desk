import json

from flask import Flask, g, render_template, request, redirect, session, url_for, flash

from db import init_db, get_connection
from auth import login_required, role_required
from rules import (
    classify_severity,
    route_to_team,
    build_escalation,
    build_handoff_summary,
    build_mock_payload,
)

app = Flask(__name__)
app.secret_key = "ops-triage-desk-dev-session-key"  # change in production

# Ensure the database is initialised at startup
init_db()


@app.before_request
def load_current_user():
    """Attach the current user's database row to `g.user` when logged in."""
    if "user_id" not in session:
        g.user = None
        return
    conn = get_connection()
    try:
        g.user = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("triage"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_connection()
        try:
            user = conn.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        finally:
            conn.close()

        from werkzeug.security import check_password_hash

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("triage"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------

@app.route("/triage")
@login_required
def triage():
    return render_template("index.html")


@app.route("/triage/submit", methods=["POST"])
@login_required
def triage_submit():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    business_area = request.form.get("business_area", "").strip()
    system_affected = request.form.get("system_affected", "").strip()
    impact_level = request.form.get("impact_level", "")
    urgency = request.form.get("urgency", "")
    customer_impact = request.form.get("customer_impact", "")

    if not all([title, description, business_area, system_affected,
                impact_level, urgency, customer_impact]):
        flash("All fields are required.", "danger")
        return redirect(url_for("triage"))

    severity, severity_description = classify_severity(impact_level, urgency, customer_impact)
    suggested_team = route_to_team(title, description)
    escalation_recommendation = build_escalation(severity)
    mock_payload = build_mock_payload(dict(
        title=title,
        description=description,
        business_area=business_area,
        system_affected=system_affected,
        impact_level=impact_level,
        urgency=urgency,
        customer_impact=customer_impact,
        severity=severity,
        severity_description=severity_description,
        suggested_team=suggested_team,
        escalation_recommendation=escalation_recommendation,
        submitted_by=session["username"],
        handoff_summary="",  # filled below
    ))
    handoff_summary = build_handoff_summary({
        "title": title,
        "business_area": business_area,
        "system_affected": system_affected,
        "impact_level": impact_level,
        "urgency": urgency,
        "customer_impact": customer_impact,
        "severity": severity,
        "severity_description": severity_description,
        "suggested_team": suggested_team,
    })
    mock_payload["handoff_summary"] = handoff_summary

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO incidents (
                title, description, business_area, system_affected,
                impact_level, urgency, customer_impact,
                severity, severity_description, suggested_team,
                escalation_recommendation, handoff_summary, mock_payload,
                submitted_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title, description, business_area, system_affected,
                impact_level, urgency, customer_impact,
                severity, severity_description, suggested_team,
                escalation_recommendation, handoff_summary,
                json.dumps(mock_payload),
                session["username"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return render_template(
        "result.html",
        result=dict(
            title=title,
            description=description,
            business_area=business_area,
            system_affected=system_affected,
            impact_level=impact_level,
            urgency=urgency,
            customer_impact=customer_impact,
            severity=severity,
            severity_description=severity_description,
            suggested_team=suggested_team,
            escalation_recommendation=escalation_recommendation,
            handoff_summary=handoff_summary,
            mock_payload=mock_payload,
        ),
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

@app.route("/audit")
@login_required
def audit():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, severity, submitted_by, submitted_at FROM incidents ORDER BY submitted_at DESC"
        ).fetchall()
        return render_template("audit.html", incidents=rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin (supervisor only)
# ---------------------------------------------------------------------------

@app.route("/admin")
@role_required("supervisor")
def admin():
    return render_template("admin.html")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
