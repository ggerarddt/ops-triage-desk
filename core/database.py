"""Database access helpers — lightweight, explicit, no global state."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "incidents.db")

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _get_conn(db_path: str | None = None) -> sqlite3.Connection:
    """Return a new sqlite3 connection with Row factory."""
    path = db_path or DATABASE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def session(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields and rolls back on exception, commits on success."""
    conn = _get_conn(db_path)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

SCHEMA_SQL: str = """\
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('operator', 'supervisor'))
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    business_area TEXT NOT NULL,
    system_affected TEXT NOT NULL,
    impact_level TEXT NOT NULL CHECK(impact_level IN ('low', 'medium', 'high')),
    urgency TEXT NOT NULL CHECK(urgency IN ('low', 'medium', 'high')),
    customer_impact TEXT NOT NULL CHECK(customer_impact IN ('yes', 'no')),
    severity TEXT,
    severity_description TEXT,
    suggested_team TEXT,
    escalation_recommendation TEXT,
    handoff_summary TEXT,
    mock_payload TEXT,
    submitted_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'approved',
    severity_level INTEGER NOT NULL DEFAULT 4,
    submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    incident_id INTEGER,
    severity TEXT,
    team TEXT,
    action TEXT NOT NULL,
    reason TEXT
);
"""


def init_schema(db_path: str | None = None) -> None:
    """Execute schema DDL so tables exist before any app code runs."""
    with session(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

INSERT_USER_SQL: str = "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)"


def seed_users(users: list[tuple[str, str, str]], db_path: str | None = None) -> None:
    """Insert seed user rows; ignores duplicates by PK."""
    with session(db_path) as conn:
        conn.executemany(INSERT_USER_SQL, users)


# ---------------------------------------------------------------------------
# Incident persistence
# ---------------------------------------------------------------------------

INSERT_INCIDENT_SQL: str = """\
INSERT INTO incidents (
    title, description, business_area, system_affected,
    impact_level, urgency, customer_impact,
    severity, severity_description, suggested_team,
    escalation_recommendation, handoff_summary, mock_payload,
    submitted_by, status, severity_level
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

def severity_to_level(severity_label: str) -> int:
    """Map a severity label like P1 -> 1, P4 -> 4."""
    return int(severity_label.lstrip("P")) if severity_label and severity_label.startswith("P") else 4

INSERT_AUDIT_LOG_SQL: str = """\
INSERT INTO audit_log (username, role, incident_id, severity, team, action, reason)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""


def save_incident(incident: dict, db_path: str | None = None) -> None:
    """Persist a fully-classified incident with approval status."""
    with session(db_path) as conn:
        conn.execute(INSERT_INCIDENT_SQL, (
            incident["title"],
            incident["description"],
            incident["business_area"],
            incident["system_affected"],
            incident["impact_level"],
            incident["urgency"],
            incident["customer_impact"],
            incident["severity"],
            incident["severity_description"],
            incident["suggested_team"],
            incident["escalation_recommendation"],
            incident["handoff_summary"],
            incident["mock_payload"],
            incident["submitted_by"],
            incident.get("status", "approved"),
            severity_to_level(incident.get("severity", "P4")),
        ))


def list_incidents(db_path: str | None = None) -> list[sqlite3.Row]:
    """Return the newest incident log rows with status and severity info."""
    with session(db_path) as conn:
        return conn.execute(
            "SELECT id, title, severity, severity_level, submitted_by, submitted_at, status"
            " FROM incidents ORDER BY submitted_at DESC"
        ).fetchall()


def save_audit_log(entry: dict, db_path: str | None = None) -> None:
    """Record an audit trail entry."""
    with session(db_path) as conn:
        conn.execute(INSERT_AUDIT_LOG_SQL, (
            entry["username"],
            entry["role"],
            entry["incident_id"],
            entry.get("severity"),
            entry.get("team"),
            entry["action"],
            entry.get("reason"),
        ))


def list_audit_log(limit: int = 50, db_path: str | None = None) -> list[sqlite3.Row]:
    """Return recent audit log entries."""
    with session(db_path) as conn:
        return conn.execute(
            "SELECT id, timestamp, username, role, incident_id, severity, team, action, reason"
            " FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
