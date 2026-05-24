from functools import wraps
from flask import flash, redirect, url_for, session


def login_required(f):
    """Decorator that redirects to login when the user is not authenticated."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator that restricts access to users with one of the listed roles."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("triage"))
            return f(*args, **kwargs)

        return decorated

    return decorator
