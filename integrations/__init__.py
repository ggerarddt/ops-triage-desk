"""Integration adapter for building mock outbound payloads.

Does not perform a real HTTP call — it only constructs the serialisable
dict that a ticketing or workflow system would accept.
"""
from __future__ import annotations

from integrations.mock_integrator import build_mock_payload
