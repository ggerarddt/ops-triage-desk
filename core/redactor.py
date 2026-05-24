"""Sensitive data redaction for logging.

Scans strings for patterns that commonly appear in incident descriptions
(email addresses, US phone numbers, SSNs, credit card-like numbers) and
replaces each match with a redaction marker.

Designed to run on log-boundary strings only — not on every keystroke.
"""
from __future__ import annotations

import re

# Regex patterns — compiled once at import time.
_PATTERNS: list[tuple[re.Pattern, str]] = [
    # US SSN: NNN-NN-NNNN
    (
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN REDACTED]",
    ),
    # US phone: (XXX) XXX-XXXX or XXX-XXX-XXXX or XXX.XXX.XXXX
    (
        re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "[PHONE REDACTED]",
    ),
    # Credit card-like: groups of digits separated by spaces or dashes
    (
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "[CARD REDACTED]",
    ),
    # Email addresses
    (
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        "[EMAIL REDACTED]",
    ),
]


def redact(text: str) -> str:
    """Return *text* with known PII patterns replaced by markers.

    Does not raise on bad input; returns the original string if
    replacement is not possible.
    """
    if text is None:
        return ""
    if text == "":
        return ""
    result: str = str(text)
    try:
        for pattern, marker in _PATTERNS:
            result = pattern.sub(marker, result)
    except Exception:
        result = str(text)
    return result
