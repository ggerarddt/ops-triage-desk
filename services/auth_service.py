"""Authentication service — user lookup and password verification.

Uses core.database for access and Werkzeug for hashing.
No Flask dependency (the decorator lives in router.py).
"""
from __future__ import annotations

from werkzeug.security import check_password_hash

from core.database import session


def find_user_by_username(username: str) -> dict | None:
    """Look up a user row by username, or None."""
    with session() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return dict(row) if row else None


def verify_password(user: dict, password: str) -> bool:
    """Compare plaintext *password* against the user's stored hash."""
    return check_password_hash(user["password_hash"], password)
