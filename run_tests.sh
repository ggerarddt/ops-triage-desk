#!/usr/bin/env bash
# Run the full test suite for the Incident Triage Desk.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
python -m pytest "$SCRIPT_DIR/tests" -v "$@"
