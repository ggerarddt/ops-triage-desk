import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "incidents.db")

ROLES = ("operator", "supervisor")

SEED_USERS = [
    ("operator1", generate_password_hash("ChangeMe123!"), "operator"),
    ("operator2", generate_password_hash("ChangeMe123!"), "operator"),
    ("supervisor1", generate_password_hash("ChangeMe123!"), "supervisor"),
]


def get_connection(db_path=None):
    """Return a new sqlite3 connection with Row factory."""
    path = db_path or DATABASE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path=None):
    """Create tables if they do not exist and seed demo users."""
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('operator', 'supervisor'))
            )
        """)
        conn.execute("""
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
                submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # Seed users only if the table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            for username, password_hash, role in SEED_USERS:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role),
                )
        conn.commit()
    finally:
        conn.close()
