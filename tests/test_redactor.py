"""Tests for sensitive data redaction (governance feature)."""
import pytest

from core.redactor import redact


class TestRedactEmail:
    def test_single_email(self):
        text = "Contact john@example.com for details"
        result = redact(text)
        assert "john@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_multiple_emails(self):
        text = "Reach out to a@b.com or c@d.org"
        result = redact(text)
        assert result.count("[EMAIL REDACTED]") == 2

    def test_no_email(self):
        text = "No emails here"
        assert redact(text) == text

    def test_null_input(self):
        assert redact(None) == ""

    def test_empty_string(self):
        assert redact("") == ""


class TestRedactPhone:
    def test_parenthetical_phone(self):
        result = redact("(555) 123-4567")
        assert "[PHONE REDACTED]" in result
        assert "555" not in result

    def test_dash_phone(self):
        result = redact("555-123-4567")
        assert "[PHONE REDACTED]" in result

    def test_dot_phone(self):
        result = redact("555.123.4567")
        assert "[PHONE REDACTED]" in result


class TestRedactSSN:
    def test_ssn_pattern(self):
        result = redact("SSN is 123-45-6789")
        assert "[SSN REDACTED]" in result
        assert "123-45-6789" not in result

    def test_ssn_in_text(self):
        result = redact("Contact 123-45-6789 for verification")
        assert "[SSN REDACTED]" in result


class TestRedactCreditCard:
    def test_cc_with_dashes(self):
        result = redact("Card: 1234-5678-9012-3456")
        assert "[CARD REDACTED]" in result

    def test_cc_with_spaces(self):
        result = redact("Card: 1234 5678 9012 3456")
        assert "[CARD REDACTED]" in result


class TestRedactMixed:
    def test_email_and_phone(self):
        result = redact("email: user@test.com phone: 555-123-4567")
        assert "[EMAIL REDACTED]" in result
        assert "[PHONE REDACTED]" in result
        assert "user@test.com" not in result
        assert "555-123-4567" not in result

    def test_no_special_patterns_unchanged(self):
        text = "Database query failed with timeout after 30 seconds"
        assert redact(text) == text
