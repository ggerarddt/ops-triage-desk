# Ops-Triage-Desk

Operational Incident Triage Desk — a lightweight, browser-based internal tool for ops teams to submit, classify, review, and resolve operational incidents without requiring external integrations.

## Purpose

Automate the first triage step of the incident management process: ingest incident reports, classify severity, route to the right team, and surface high-priority (P1) items for supervisor review. The tool is designed as an enterprise-style demo that demonstrates governance, audit, and workflow controls without adding external dependencies.

## Business Scenario

An ops team receives incident reports that must be quickly classified, routed to the correct team, escalated for supervisor review when severity is high (P1), and tracked in an audit log for compliance and post-incident review. This tool handles that entire flow in-memory with SQLite persistence.

## Seeded Users

| Username | Password | Role |
|---|---|---|
| `operator1` | `ChangeMe123!` | operator |
| `operator2` | `ChangeMe123!` | operator |
| `supervisor1` | `ChangeMe123!` | supervisor |

Operators can submit incidents. P1 escalations require supervisor approval before becoming actionable. Supervisors have access to the admin dashboard for review, approval, denial, reclassification, and editing of pending P1 incidents.

## Main Features

- **Incident Submission** — Web form and JSON API for submitting incidents with automatic severity classification and team routing
- **Governance Controls** — Input validation, field length limits, allowed values
- **P1 Approval Gate** — Operator P1 incidents require supervisor approval; non-P1 auto-approve
- **Audit Trail** — Every submission and admin action is recorded in SQLite
- **Administrative Operations** — Approve, deny, reclassify, and edit pending P1 incidents
- **PII Redaction** — Automatically redacts emails, phone numbers, SSNs, and credit card patterns from logs
- **Policy Banner** — "Decision support only" banner on every page, reminding users of human ownership

## Architecture Summary

```
app.py          — Small Flask bootstrap (schema init, seed, routes)
router.py       — HTTP routes, session, decorators
core/
  database.py   — Schema DDL, seed data, all SQLite queries
  config.py     — Severity rules, team keywords, escalation policy
  gov_config.py — Governance constants (statuses, limits, thresholds)
  redactor.py   — PII redaction
services/
  triage_service.py   — End-to-end triage pipeline orchestration
  severity_service.py — classify_severity(impact, urgency, customer_impact)
  routing_service.py  — route_team(title, description) keyword scoring
  validation.py       — validate_incident_input()
  auth_service.py     — find_user_by_username, verify_password
templates/    — Jinja2 HTML templates (no external CSS/JS framework)
integrations/ — Mock integrator (builds a JSON payload that simulates external handoff)
tests/        — Full pytest suite with module-scoped test SQLite DB
```

### Request Flows

| Scenario | Flow |
|---|---|
| Login | `/login` POST → `auth_service.find_user_by_username` → `auth_service.verify_password` → set session |
| Web Triage | `/triage` GET → `index.html` → POST `/triage/submit` → `validation.validate_incident_input` → `classification.classify_severity` → `routing.route_team` → `handoff.build_handoff_summary` → `database.save_incident` → `admin.save_audit_log` |
| JSON Triage | `/api/triage` POST → same pipeline, returns JSON |
| Admin Approval | `/admin` GET → `database.get_pending_p1s` → render dashboard |
| Admin Approve | `/admin/approve` POST → `database.approve` → `database.save_audit_log` → redirect |
| Admin Deny | `/admin/deny` POST → `database.deny` → `database.save_audit_log` → redirect |
| Admin Reclassify | `/admin/reclassify` POST → `database.reclassify` → `database.save_audit_log` → redirect |
| Admin Edit | `/admin/edit/<id>` GET → show form → POST → update fields → reclassify if severity changed → `database.save_audit_log` |

## Severity Classification

| Impact | Urgency | Customer Impact | Severity |
|---|---|---|---|
| High | * | * | P1 |
| Medium | High | Yes | P1 |
| Medium | Low/High | No | P2 |
| Medium/Low | Low | * | P3 |
| Low | Low | * | P4 |

## Team Routing

Keywords in title/description are scored per team; the team with the highest overlap wins. Ties go to infrastructure.

## Mock Integration

Each submission generates a JSON payload simulating what would be sent to PagerDuty, Slack, or an issue tracker. The `mock_payload` field is included in the result for inspection but is never actually transmitted.

## Logging and Redaction

Structured `logger.info` calls on triage events. The PII redactor runs on description before logging.

## Audit Trail

All submissions, approvals, denials, reclassifications, and edits are recorded in the `audit_log` table with timestamp, username, role, severity, team, action, and reason.

## Governance and Admin Controls

- Input validation with field limits and allowed values
- P1 approval gate enforced by role
- Supervisor-only admin dashboard
- Reclassification only to P2/P3/P4
- Denial requires a reason
- All admin actions logged to audit trail

## Limitations

- **Demo authentication** — No LDAP, SSO, or 2FA; passwords stored as werkzeug hashes locally
- **Local SQLite state** — No HA, no replication, no external DB connection
- **No CSRF protection** — No CSRF tokens are implemented
- **Mock integration only** — Never contacts external systems
- **Local deployment only** — No container or cloud deployment support

## How to Run Locally

```bash
cd /home/demouser/demos/ops-triage-desk
python app.py
```

Navigate to http://localhost:5000

## How to Run Tests

```bash
python -m pytest tests/ -v
```

Run only a specific test file:
```bash
python -m pytest tests/test_admin.py -v
python -m pytest tests/test_governance.py -v
```
