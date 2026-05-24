"""Operational Incident Triage Desk.

Flask bootstrap: create the app, register routes, start the server.
"""
from __future__ import annotations

import logging
import os

from flask import Flask

from core.database import init_schema, seed_users
from core.config import SEED_USERS
from router import register_routes

# ---------------------------------------------------------------------------
# Logging (structured, severity-based)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("ops-triage")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "ops-triage-desk-dev-session-key"  # change in production

# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

init_schema()
seed_users(SEED_USERS)
logger.info("Database initialised and seed users loaded.")

# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

register_routes(app)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting triage desk on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
