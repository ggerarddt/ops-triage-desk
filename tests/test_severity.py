"""Severity classification tests.

Tests each boundary: P1, P2, P3, P4, plus edge cases.
"""
import pytest

from services.severity_service import classify_severity


class TestSeverityP1:
    """P1 = high impact, OR high urgency with customer impact yes."""

    def test_high_impact_no_customer_impact(self):
        label, desc = classify_severity("high", "low", "no")
        assert label == "P1"
        assert "Critical" in desc

    def test_high_impact_high_urgency_yes_cust(self):
        label, _ = classify_severity("high", "high", "yes")
        assert label == "P1"

    def test_medium_impact_high_urgency_yes_cust(self):
        label, _ = classify_severity("medium", "high", "yes")
        assert label == "P1"

    def test_low_impact_high_urgency_yes_cust(self):
        label, _ = classify_severity("low", "high", "yes")
        assert label == "P1"


class TestSeverityP2:
    """P2 = high impact without customer impact OR medium impact + high urgency."""

    def test_high_impact_all_cases_are_p1(self):
        # P1 rules catch ALL high impact cases first.
        # This test confirms the boundary that nothing with high impact can be P2.
        label, _ = classify_severity("high", "high", "yes")
        assert label == "P1"
        label, _ = classify_severity("high", "high", "no")
        assert label == "P1"
        label, _ = classify_severity("high", "low", "no")
        assert label == "P1"
        label, _ = classify_severity("high", "medium", "yes")
        assert label == "P1"

    def test_medium_impact_high_urgency_no_cust(self):
        # high urgency + medium impact = P1 when customer=yes, but P2 when customer=no
        label, _ = classify_severity("medium", "high", "no")
        assert label == "P2"

    def test_high_impact_low_urgency_no_cust(self):
        # P1: high impact -> takes priority, so this is P1
        label, _ = classify_severity("high", "low", "no")
        assert label == "P1"  # P1 catches ALL high impact


class TestSeverityP3:
    """P3 = medium impact OR medium urgency."""

    def test_medium_impact_low_urgency(self):
        label, _ = classify_severity("medium", "low", "no")
        assert label == "P3"

    def test_low_impact_medium_urgency(self):
        label, _ = classify_severity("low", "medium", "no")
        assert label == "P3"

    def test_low_impact_medium_urgency_customer_yes(self):
        label, _ = classify_severity("low", "medium", "yes")
        assert label == "P3"


class TestSeverityP4:
    """P4 = everything else (low + low)."""

    def test_low_low(self):
        label, desc = classify_severity("low", "low", "no")
        assert label == "P4"
        assert "Minor" in desc

    def test_low_low_customer_yes(self):
        label, _ = classify_severity("low", "low", "yes")
        assert label == "P4"


class TestSeverityEdgeCases:
    """Edge cases: empty strings, unexpected casing, unknown severity."""

    def test_empty_strings(self):
        label, _ = classify_severity("", "", "")
        # Falls through to P4 (default fallback)
        assert label == "P4"

    def test_uppercase_impact(self):
        """Unexpected casing should not match normalised rules."""
        label, _ = classify_severity("HIGH", "HIGH", "YES")
        # Rules expect lowercase; HIGH != high so falls through to P4
        assert label == "P4"

    def test_low_high_urgency_no_customer(self):
        """low impact, high urgency, no customer != P1 (P1 requires customer=yes for high urgency).
        Falls through to P4 since no P2/P3 rule matches."""
        label, _ = classify_severity("low", "high", "no")
        assert label == "P4"
