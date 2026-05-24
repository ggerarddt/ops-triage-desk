# Operational Incident Triage Desk

A small Flask web application for ops staff to submit incident reports and
receive automated severity classification, routing, and mock ticketing payloads.
Fully local — no external services required.

## Project Structure

```
app.py                  # Flask bootstrap: create app, register routes
router.py               # Route definitions: login, triage, audit, admin, API
core/
  __init__.py
  models.py             # Incident, TriageResult, User dataclasses
  config.py             # Severity descriptions, team keywords, escalation, seed data
  database.py           # SQLite connection, schema init, seed loading
  summary_service.py    # Handoff summary builder
services/
  __init__.py
  auth_service.py       # User lookup and password verification
  severity_service.py   # classify_severity()
  routing_service.py    # route_team(), escalation_recommendation()
  triage_service.py     # Full triage pipeline orchestration
integrations/
  mock_integrator.py    # build_mock_payload() (no network I/O)
templates/              # Jinja2 templates (login, index, result, audit, admin)
static/app.js           # Example button auto-fill
requirements.txt        # Python dependencies
```

## Engineering Highlights

- **Separation of concerns**: HTTP/UI code lives in `router.py`; business logic
  in `services/`; persistence in `core/database.py`; configuration in `core/config.py`.
- **Domain models**: `Incident`, `TriageResult`, `User` dataclasses in `core/models.py`.
- **Structured logging**: Every triage completion logs severity and team.
  Sensitive descriptions are not logged.
- **JSON API**: `POST /api/triage` accepts and returns JSON for downstream automation.
- **No external services**: SQLite, Werkzeug, Python stdlib only.

## Quick Start

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Open in a browser
#    http://localhost:5000
```

## Default Users

| Username | Password | Role |
|---|---|---|
| operator1 | `ChangeMe123!` | operator |
| operator2 | `ChangeMe123!` | operator |
| supervisor1 | `ChangeMe123!` | supervisor |

### Role Access

- **Operators** → `/triage`, `/audit`
- **Supervisors** → `/triage`, `/audit`, `/admin`

## Severity Rules

| Severity | Condition |
|---|---|
| P1 | High impact **or** High urgency with customer impact = yes |
| P2 | High impact without customer impact, or Medium impact + High urgency |
| P3 | Medium impact **or** Medium urgency |
| P4 | Everything else (Low + Low) |

## Routing (keyword-based)

Keywords in the title or description map to teams:

- **API Integration Team** — api, rest, endpoint, 502, 503, webhook, etc.
- **Data Platform Team** — pipeline, etl, data warehouse, database, etc.
- **Customer Operations** — customer, user, billing, support, etc.
- **Infrastructure Team** — server, disk, cpu, network, deployment, etc.

## Database

The SQLite file `incidents.db` is created automatically on first run.
Tables: `users`, `incidents`.
