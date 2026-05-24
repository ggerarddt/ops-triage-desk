# Operational Incident Triage Desk — Quick-Start

A small Flask web application for ops staff to submit incident reports and
receive automated severity classification, routing, and mock ticketing payloads.
Fully local — no external services required.

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Flask routes — login, triage, audit, admin |
| `db.py` | SQLite schema, init, and seed data |
| `auth.py` | `@login_required` and `@role_required` decorators |
| `rules.py` | Severity classification, keyword routing, handoff helpers |
| `templates/login.html` | Login form |
| `templates/index.html` | Triage form + quick-load example buttons |
| `templates/result.html` | Classification result view |
| `templates/audit.html` | Incident audit log |
| `templates/admin.html` | Supervisor-only placeholder admin page |
| `static/app.js` | Client-side example-button auto-fill |
| `requirements.txt` | Python dependencies |

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
