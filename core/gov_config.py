"""Governance configuration for the Incident Triage Desk.

All tunable policy constants that affect validation, approval gates, and
output formatting live here so they can be inspected or changed without
touching business logic.
"""

# ---------------------------------------------------------------------------
# Allowed form values
# ---------------------------------------------------------------------------

ALLOWED_IMPACT_VALUES = ("low", "medium", "high")
ALLOWED_URGENCY_VALUES = ("low", "medium", "high")
ALLOWED_CUSTOMER_IMPACT_VALUES = ("yes", "no")

# ---------------------------------------------------------------------------
# Field length limits
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH = 250
MAX_DESCRIPTION_LENGTH = 5000
MAX_SYSTEM_AFFECTED_LENGTH = 200
MAX_BUSINESS_AREA_LENGTH = 150

# ---------------------------------------------------------------------------
# P1 approval gate
# ---------------------------------------------------------------------------

P1_APPROVAL_ENABLED = True

# Approval status constants
APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_DENIED = "denied"
APPROVAL_STATUS_REJECTED = "rejected"
APPROVAL_STATUS_RECLASSIFIED = "reclassified"

# Allowed reclassification targets (must be lower than P1)
ALLOWED_RECLASSIFY_TARGETS = ("P2", "P3", "P4")

# Admin-specific constants
ADMINS = ["supervisor1"]
ADMIN_PASSWORD = "ChangeMe123!"
