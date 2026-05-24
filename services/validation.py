"""Validation helpers for incident input.

Used by route handlers (form and JSON API) to validate and return
friendly error responses before any business logic runs.
"""
from __future__ import annotations

from core.gov_config import (
    ALLOWED_IMPACT_VALUES,
    ALLOWED_URGENCY_VALUES,
    ALLOWED_CUSTOMER_IMPACT_VALUES,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_SYSTEM_AFFECTED_LENGTH,
    MAX_BUSINESS_AREA_LENGTH,
)


class ValidationError:
    """Represents a single validation error."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def __repr__(self):
        return f"ValidationError({self.field!r}, {self.message!r})"


def validate_incident_input(
    title: str,
    description: str,
    business_area: str,
    system_affected: str,
    impact_level: str,
    urgency: str,
    customer_impact: str,
) -> list[ValidationError]:
    """Validate incident fields.  Returns a list of errors (empty == valid)."""
    errors: list[ValidationError] = []

    # Presence checks
    if not title or not title.strip():
        errors.append(ValidationError("title", "Title is required."))
    if not description or not description.strip():
        errors.append(ValidationError("description", "Description is required."))

    # Length checks
    title_stripped = (title or "").strip()
    description_stripped = (description or "").strip()
    if len(title_stripped) > MAX_TITLE_LENGTH:
        errors.append(ValidationError(
            "title",
            f"Title must be {MAX_TITLE_LENGTH} characters or fewer.",
        ))
    if len(description_stripped) > MAX_DESCRIPTION_LENGTH:
        errors.append(ValidationError(
            "description",
            f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.",
        ))

    # Business area & system affected length
    if business_area and len(business_area.strip()) > MAX_BUSINESS_AREA_LENGTH:
        errors.append(ValidationError(
            "business_area",
            f"Business area must be {MAX_BUSINESS_AREA_LENGTH} characters or fewer.",
        ))
    if system_affected and len(system_affected.strip()) > MAX_SYSTEM_AFFECTED_LENGTH:
        errors.append(ValidationError(
            "system_affected",
            f"System affected must be {MAX_SYSTEM_AFFECTED_LENGTH} characters or fewer.",
        ))

    # Allowed values
    if impact_level not in ALLOWED_IMPACT_VALUES:
        errors.append(ValidationError(
            "impact_level",
            f"Impact level must be one of: {', '.join(ALLOWED_IMPACT_VALUES)}.",
        ))
    if urgency not in ALLOWED_URGENCY_VALUES:
        errors.append(ValidationError(
            "urgency",
            f"Urgency must be one of: {', '.join(ALLOWED_URGENCY_VALUES)}.",
        ))
    if customer_impact not in ALLOWED_CUSTOMER_IMPACT_VALUES:
        errors.append(ValidationError(
            "customer_impact",
            f"Customer impact must be one of: {', '.join(ALLOWED_CUSTOMER_IMPACT_VALUES)}.",
        ))

    return errors
