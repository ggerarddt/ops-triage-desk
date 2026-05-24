"""Tests for input validation (governance feature)."""
import pytest

from services.validation import validate_incident_input, ValidationError
from core.gov_config import (
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    ALLOWED_IMPACT_VALUES,
    ALLOWED_URGENCY_VALUES,
    ALLOWED_CUSTOMER_IMPACT_VALUES,
)


class TestValidationPresence:
    def test_empty_title(self):
        errs = validate_incident_input("", "desc", "BA", "SYS", "low", "low", "no")
        assert any(e.field == "title" for e in errs)

    def test_whitespace_title(self):
        errs = validate_incident_input("   ", "desc", "BA", "SYS", "low", "low", "no")
        assert any(e.field == "title" for e in errs)

    def test_empty_description(self):
        errs = validate_incident_input("title", "", "BA", "SYS", "low", "low", "no")
        assert any(e.field == "description" for e in errs)

    def test_all_required_present(self):
        errs = validate_incident_input("T", "D", "BA", "S", "low", "low", "no")
        assert all(e.field not in ("title", "description") for e in errs)


class TestValidationLengths:
    def test_too_long_title(self):
        title = "A" * (MAX_TITLE_LENGTH + 1)
        errs = validate_incident_input(title, "desc", "BA", "SYS", "low", "low", "no")
        assert any(e.field == "title" for e in errs)

    def test_too_long_description(self):
        desc = "A" * (MAX_DESCRIPTION_LENGTH + 1)
        errs = validate_incident_input("t", desc, "BA", "SYS", "low", "low", "no")
        assert any(e.field == "description" for e in errs)

    def test_ok_lengths(self):
        title = "A" * MAX_TITLE_LENGTH
        desc = "A" * MAX_DESCRIPTION_LENGTH
        errs = validate_incident_input(title, desc, "BA", "SYS", "low", "low", "no")
        assert all(e.field not in ("title", "description") for e in errs)


class TestValidationAllowedValues:
    def test_invalid_impact(self):
        errs = validate_incident_input("t", "d", "BA", "S", "critical", "low", "no")
        assert any(e.field == "impact_level" for e in errs)

    def test_valid_impact_values(self):
        for val in ALLOWED_IMPACT_VALUES:
            errs = validate_incident_input("t", "d", "BA", "S", val, "low", "no")
            assert all(e.field != "impact_level" for e in errs)

    def test_invalid_urgency(self):
        errs = validate_incident_input("t", "d", "BA", "S", "low", "urgent", "no")
        assert any(e.field == "urgency" for e in errs)

    def test_invalid_customer_impact(self):
        errs = validate_incident_input("t", "d", "BA", "S", "low", "low", "maybe")
        assert any(e.field == "customer_impact" for e in errs)

    def test_valid_customer_impact_values(self):
        for val in ALLOWED_CUSTOMER_IMPACT_VALUES:
            errs = validate_incident_input("t", "d", "BA", "S", "low", "low", val)
            assert all(e.field != "customer_impact" for e in errs)


class TestValidationErrorsAreList:
    def test_multiple_errors_returned(self):
        errs = validate_incident_input("", "   ", "BA", "S", "x", "y", "z")
        assert isinstance(errs, list)
        assert len(errs) >= 2

    def test_error_has_field_and_message(self):
        errs = validate_incident_input("", "T", "BA", "S", "low", "low", "no")
        err = errs[0]
        assert hasattr(err, "field")
        assert hasattr(err, "message")
        assert isinstance(err.field, str)
        assert isinstance(err.message, str)
