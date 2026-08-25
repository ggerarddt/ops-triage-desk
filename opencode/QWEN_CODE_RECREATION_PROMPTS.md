# Ops-Triage-Desk — Qwen Code Recreation Prompts

## Reverse-Engineered Development History

| PR | Branch | Focus | Key Deliverable |
|----|--------|-------|-----------------|
| #1 | `feat/1-prototype` | Prototype | Flat Flask app: db.py, auth.py, rules.py, templates, JS auto-fill |
| #2 | `feat/2-refactor` | Architecture | Split into core/ services/ integrations/, dataclasses, JSON API, router.py |
| #3 | `feat/3-tests` | Tests | 60+ pytest tests, 5 modules, temp-fixture isolation |
| #4 | `feat/4-governance` | Governance | Validation, PII redaction, audit log, P1 approval gate |
| #5 | `feat/5-admin` | Admin UX | Supervisor dashboard, approve/deny/reclassify/edit |
| #6 | `feat/6-polish` (optional) | Docs & cleanup | ARCHITECTURE.md, smoke test, final quality pass |

**Evolution logic:**
- PR 1 proves the *idea* (rules work, UI works, users authenticate).
- PR 2 proves *structure* without changing behavior (separation of concerns).
- PR 3 proves *reliability* (tests catch regressions in all layers).
- PR 4 proves *governance* (enterprise controls visible in the product).
- PR 5 proves *completeness* (workflow is end-to-end, auditable, editable).
- PR 6 (optional) proves it is *shippable* (documented, smoke-tested, clean).

**Hard rule:** Each prompt ends with a PR. The next prompt does not begin until the human has
reviewed, approved, and merged that PR. No prompt may be merged on the agent's own authority.

---

## How to Use

For each prompt (in order):

1. Open a fresh Qwen Code session in the project directory.
2. Paste the prompt.
3. The agent will: create the feature branch → implement → test → push → create the PR → **stop**.
4. **Human step (required):** Review the PR in your terminal or browser.
   - Terminal:   `gh pr view <n>`
   - Browser:    open the PR URL shown by the agent.
   - Approve:    `gh pr review <n> --approve`   or click **Review** → **Approve** in the browser.
   - Merge:      `gh pr merge <n> --squash`     or click **Merge pull request** in the browser.
5. Only after the merge is complete, open the next prompt. The next prompt's
   guardrails will verify the previous PR is merged before doing any work.

---

## Common Guardrails

The following two blocks appear at the top and bottom of every prompt.
They are spelled out in each prompt so no context is needed to understand the workflow.

### START — verify repository state (Prompts 2–6)

```
## STEP 0 — Verify Repository State (run before anything else)

STOP if any of the following checks fail; report the failure to the user and wait for instruction.

1. Confirm the git remote exists:
     git remote -v
   → must show an origin URL containing github.com

2. Detect the default branch (do NOT assume it is named main or master):
     gh repo view --json nameWithOwner,defaultBranchRef -q '.defaultBranchRef.name'

3. Confirm the PREVIOUS prompt's PR is MERGED (not just closed):
     gh pr list --state merged --limit 3
   → the most recent entry must correspond to the previous prompt.
   If it is not merged, STOP: "The previous PR is not yet merged.
   Please approve and merge it before proceeding."

4. Clean working tree:
     git status --short
   → must print nothing. If there are uncommitted changes, STOP and ask the user what to do.

5. Switch to the default branch and pull:
     git checkout <default-branch>
     git pull --ff-only origin <default-branch>

6. Create the feature branch for THIS prompt:
     git checkout -b feat/<n>-<slug>

Only after all 6 steps pass, begin implementation.
```

### END — push, open PR, stop (all prompts)

```
## FINAL STEPS — Push, Open PR, and Stop

Run in strict order. Do NOT skip any step.

Before running Python commands, ensure the virtual environment is active:
     source .venv/bin/activate   # only needed if not already active in the shell session

1. Run the full test suite one final time; all tests must pass:
     python -m pytest tests/ -v

2. Smoke test — start the app and verify at least login + one page render; then stop it:
     python app.py          # confirm "Running on http://..." with no errors; Ctrl+C to stop

3. Stage and commit (only intended files):
     git add .
     git commit -m "<conventional commit message>"

4. Inspect the commit:
     git show --stat HEAD
   → confirm no .pyc, incidents.db, or other unwanted files are present.

5. Push the feature branch:
     git push -u origin <feature-branch>

6. Open the pull request:
     gh pr create \
       --base <default-branch> \
       --head <feature-branch> \
       --title "<PR title>" \
       --body "<structured body — see below>"

7. Verify the PR exists and report its URL to the user:
     gh pr view <pr-number>

8. STOP. Do NOT merge the PR. Do NOT start the next prompt.

   Tell the user:
   "PR #<n> is open. Please review, approve, and merge it.
    The next prompt will begin only after the PR is merged."

The human is the gate. The next prompt's STEP 0 will verify the merge before proceeding.
```

### PR body structure

```
## Summary
<One or two sentences describing what this PR adds.>

## What's Changed
- <bullet point 1>
- <bullet point 2>
...

## Acceptance Criteria
- [x] <criterion 1>
- [x] <criterion 2>
- [ ] <criterion that could not be automated, with note on how it was manually verified>

## Tests
Command:  python -m pytest tests/ -v
Results:  <N> passed, 0 failed

## Manual Smoke Test
<1–3 sentences on what was manually checked in the running app.>

## Risk & Rollback
- Risk: <low/medium/high — with reason>
- Rollback: `git revert <merge-commit>` or `gh pr close <n>`
```

---

## Prompt 1 — Prototype

```
Build a lightweight Flask web application called "Operational Incident Triage Desk."

============================================================
STEP 0 — INITIALISE REPOSITORY (first prompt only)
============================================================

This is a brand-new project. There is no existing git repository.

1. Create a minimal main branch first so there is something to branch from:

     # Ensure the working directory is the project root (empty or has only .gitignore)

     # Write .gitignore (create if missing):
     #   incidents.db
     #   __pycache__/
     #   *.pyc
     #   *.pyo
     #   .pytest_cache/
     #   .venv/
     #   .aider/
     #   .opencode/

     # Write a one-line README.md placeholder:
     #   # Ops-Triage-Desk

     git init -b main
     git add .gitignore README.md
     git commit -m "chore: initialise repository"

2. Create the GitHub repository and push main:

     gh repo create ops-triage-desk --private --source=. --remote=origin --push

   If the name is taken, try ops-triage-desk-<suffix> and report the final URL.
   If gh is not authenticated, STOP and report: "gh is not authenticated.
   Please run `gh auth login` and re-run this prompt."

3. Create the feature branch for this prompt:

     git checkout -b feat/1-prototype

4. Set up the Python environment:

     # Confirm Python 3.10 or later is available
     python3 --version
     # → must print Python 3.10.x or later. If not, STOP and report.

     # Create a virtual environment (skip if .venv already exists)
     python3 -m venv .venv

     # Activate it and install dependencies
     source .venv/bin/activate
     pip install -r requirements.txt

   Add `.venv/` to .gitignore if it is not already there (it should be).
   Confirm .venv/ is not staged in git:  git status --short  → no .venv entries.

   If any step fails, STOP and report the error. Do not proceed.

After all steps pass (steps 1–4), begin implementation.

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# Purpose
Let authenticated ops people submit an incident report and receive:
  - a severity classification (P1–P4),
  - a suggested owning team,
  - an escalation recommendation,
  - a structured one-paragraph handoff summary,
  - a mock outbound JSON payload (simulates PagerDuty/Slack/ticketing handoff).

# Tech Stack
- Python 3, Flask ≥ 3.0, Werkzeug (password hashing), SQLite via sqlite3 stdlib
- Jinja2 templates (no external CSS/JS framework)
- Plain inline CSS in templates (no Tailwind/Bootstrap)
- requirements.txt must contain: Flask>=3.0, Werkzeug>=3.0
- Do NOT add any other dependencies.

# Database
- File: incidents.db (auto-created next to app.py on first run)
- Enable WAL mode.
- Tables:
    users(id, username UNIQUE NOT NULL, password_hash NOT NULL, role NOT NULL)
    incidents(id, title, description, business_area, system_affected,
              impact_level, urgency, customer_impact,
              severity, severity_description, suggested_team,
              escalation_recommendation, handoff_summary, mock_payload,
              submitted_by, created_at)
- Seed users (hash with werkzeug.security.generate_password_hash):
    operator1   / ChangeMe123! / operator
    operator2   / ChangeMe123! / operator
    supervisor1 / ChangeMe123! / supervisor

# Severity Rules (priority-ordered; first match wins)
  P1  impact == "high"                                       (any urgency, any customer)
  P1  urgency == "high" AND customer_impact == "yes"
  P2  impact == "medium" AND urgency == "high"
  P3  impact == "medium"
  P3  urgency == "medium"
  P4  everything else

  Severity descriptions (verbatim):
    P1 = "Critical – immediate response required. High impact or high urgency with customer impact."
    P2 = "Major – prompt response needed. High impact without customer impact, or medium impact with high urgency."
    P3 = "Moderate – address within the next business cycle. Medium impact or medium urgency."
    P4 = "Minor – handle during normal operations. Low impact and low urgency."

# Team Routing (keyword scoring on lowercased title + description)
  API Integration Team:      api, rest, endpoint, http, 502, 503, gateway, integration, webhook, oauth
  Data Platform Team:        pipeline, etl, data warehouse, warehouse, database, sql,
                             dataset, schema, migration, transform, batch, disk capacity, storage
  Customer Operations Team:  customer, user, client, account, support,
                             billing, subscription, onboarding, ticket
  Infrastructure Team:       server, host, vm, disk, cpu, memory, network, dns,
                             load balancer, cluster, capacity, uptime, outage, deployment, infra
  Fallback when no keyword matches any team: Infrastructure Team

# Escalation Policy
  P1 "Page the on-call lead immediately. Open a bridge call and notify the VP
       of Engineering within 15 minutes. Provide regular updates every
       30 minutes until resolved."
  P2 "Notify the on-call engineer and team lead via Slack. Await acknowledgment
       within 30 minutes. Escalate to VP if not resolved within 2 hours."
  P3 "Create a tracked task in the team's board. Notify the team lead and
       assign for next business day."
  P4 "Log in the team's backlog. Review in the next sprint planning session."

# Routes
  GET  /              → redirect to /login if not authenticated, else /triage
  GET  /login         → login form
  POST /login         → authenticate; set session; redirect to /triage
  GET  /logout        → clear session; redirect to /login
  GET  /triage        → triage form (login required)
  POST /triage/submit → validate, classify, route, render result.html (login required)
  GET  /audit         → incident list (login required)
  GET  /admin         → supervisor-only placeholder (role required)

# Triage Form Fields (IDs must be exactly as listed — JS depends on them)
  title            (text, required)
  description      (textarea, required)
  business_area    (text)
  system_affected  (text)
  impact_level     (select: low / medium / high)
  urgency          (select: low / medium / high)
  customer_impact  (select: yes / no)

# Three Example Auto-Fill Buttons
type="button" (NOT submit). Class: example-btn.
Each button carries data-* attributes for all seven form fields.
static/app.js listens for click on .example-btn and sets
document.getElementById("<field>").value = btn.dataset.<field>

Example 1: Label="Public Admin: Benefits API 502"
  data-title="Benefits API - Intermittent 502 Errors"
  data-description="The benefits REST API is returning intermittent HTTP 502 Bad Gateway errors during peak hours. All endpoints are affected. On-call has been paged."
  data-business_area="Public Administration"
  data-system_affected="Benefits API"
  data-impact_level="high"   data-urgency="high"   data-customer_impact="yes"

Example 2: Label="Postal Service: ETL Pipeline Stalled"
  data-title="Mail Sorting ETL Pipeline Stalled"
  data-description="The nightly ETL pipeline for the mail sorting system has been stalled for 4 hours. No records are being processed or transformed into the production database."
  data-business_area="Postal Service"
  data-system_affected="Mail Sorting Data Pipeline"
  data-impact_level="medium" data-urgency="high"   data-customer_impact="no"

Example 3: Label="Research Center: Disk Capacity Warning"
  data-title="Data Warehouse Disk Capacity Warning"
  data-description="The national research data warehouse is at 92% disk capacity. The monitoring system has triggered a warning alert. If capacity is not freed, ingestion jobs will begin failing within 48 hours."
  data-business_area="National Research Center"
  data-system_affected="Data Warehouse"
  data-impact_level="high"   data-urgency="medium" data-customer_impact="no"

# Mock Integration
Build a dict (no network call) with keys:
  title, description, business_area, system_affected,
  impact_level, urgency, customer_impact (bool),
  severity, severity_description, suggested_team,
  escalation_recommendation, handoff_summary, submitted_by
Display it as pretty-printed JSON in a <pre> block on the result page.

# UI Requirements
- Navbar: brand "Incident Triage Desk" · nav links (Triage / Audit / Admin-if-supervisor)
          · role badge · username · Logout
- Policy banner on every authenticated page:
   "This tool is for internal decision support. Final ownership remains with human operators."
- Flash messages: success=green, danger=red, warning=yellow, info=blue
- Result page shows: severity label + description, suggested team, escalation text,
  handoff summary paragraph, mock JSON payload in <pre>, submitter.
- Login page: centred card, username + password, "Sign In" button.
- Inline CSS in each template (no external CSS file needed).

# File Structure (flat is acceptable for the prototype)
app.py             — Flask app, all routes, helpers
templates/
  login.html
  index.html       — triage form
  result.html      — classification result
  audit.html       — incident list
  admin.html       — supervisor placeholder
static/
  app.js           — example button behavior
requirements.txt
README.md          — how to run, seeded users, brief architecture
.gitignore

# Acceptance Criteria (verify before finishing)
  [ ] Python 3.10+ is confirmed and `.venv/` is active in the shell session
  [ ] `pip list | grep -iE "flask|werkzeug"` shows both packages installed in the venv
  [ ] `.venv/` does NOT appear in `git status --short`
  [ ] `source .venv/bin/activate && python app.py` starts on :5000 with no errors
  [ ] /login → operator1 / ChangeMe123! → redirect to /triage
  [ ] Triage page shows 3 example buttons; clicking one populates all 7 fields
  [ ] Submit form (Example 1) → result shows P1, API Integration Team, correct handoff text
  [ ] /audit shows the submitted incident
  [ ] Logout → back to /login
  [ ] Log in as supervisor1 → Admin link visible in navbar
  [ ] Log in as operator1  → Admin link NOT visible in navbar

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. Run the final acceptance checklist above. All items must be checked.

2. Stage and commit:
     git add .
     git commit -m "feat: Operational Incident Triage Desk prototype"

3. Inspect the commit:
     git show --stat HEAD

4. Push:
     git push -u origin feat/1-prototype

5. Open the pull request:
     gh pr create \
       --base main \
       --head feat/1-prototype \
       --title "feat(1): Operational Incident Triage Desk — prototype" \
       --body $(cat <<'EOF'
## Summary
Initial working prototype: Flask + SQLite auth, triage form, severity
classification (P1–P4), keyword team routing, escalation recommendations,
mock JSON payload, three auto-fill example buttons, role-based navigation.

## What's Changed
- `app.py` — full Flask application
- `templates/` — login, triage, result, audit, admin pages
- `static/app.js` — example button auto-fill
- `requirements.txt`, `README.md`, `.gitignore`

## Acceptance Criteria
- [x] App starts on :5000
- [x] Login/logout for all 3 seeded users
- [x] Triage form submits and returns P1/P2/P3/P4 classification
- [x] Team routing by keyword scoring
- [x] 3 example auto-fill buttons populate all 7 fields
- [x] Mock JSON payload displayed on result page
- [x] Role-based navbar (Admin link supervisor-only)

## Tests
No test suite yet (introduced in PR #3). Manually verified against the
acceptance checklist.

## Manual Smoke Test
- Logged in as operator1 and supervisor1.
- Clicked each example button; verified all 7 fields populated.
- Submitted Example 1 (P1/yes customer) → confirmed P1 + API Integration Team.
- Verified /audit shows the incident row.
- Verified Admin link visible for supervisor1, absent for operator1.

## Risk & Rollback
- Risk: low (prototype scope; no external dependencies)
- Rollback: `gh pr close 1`
EOF
)

6. Verify and report:
     gh pr view

7. STOP. Tell the user:
   "PR #1 is open at [URL]. Please review, approve, and merge it.
   The next prompt begins only after the PR is merged."
   Do NOT merge the PR. Do NOT proceed to the next prompt.
```

---

## Prompt 2 — Architecture Refactor

```
Refactor the Operational Incident Triage Desk into a production-shaped
architecture WITHOUT changing any user-visible behavior.

============================================================
STEP 0 — Verify Repository State
============================================================

STOP if any check fails; report to the user and wait for instruction.

1. git remote -v
   → must show github.com origin

2. Default branch:
     gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'

3. Previous PR is merged:
     gh pr list --state merged --limit 3
   → the most recent must be "feat(1): Operational Incident Triage Desk — prototype"

4. git status --short
   → must be empty

5. git checkout <default-branch> && git pull --ff-only origin <default-branch>

6. Activate the virtual environment and verify dependencies:
     source .venv/bin/activate
     pip list | grep -iE "flask|werkzeug"
   → both packages must be visible. If not, run:  pip install -r requirements.txt

7. git checkout -b feat/2-refactor

Only after all steps pass, begin implementation.

============================================================
BEFORE CHANGING ANYTHING
============================================================

Read the following files to understand current behavior:
  app.py, templates/index.html, templates/result.html, static/app.js

Confirm the acceptance checklist from Prompt 1 still passes:
  python app.py → submit Example 1 → P1 + API Integration Team → /audit shows it

Record which fields are used in templates and static/app.js so you can
verify they are preserved.

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# Target Structure
app.py               — Flask bootstrap ONLY (create app, register routes, init DB). < 40 lines.
router.py            — All route functions and HTTP parsing. Delegates to services.
core/
  __init__.py
  models.py          — @dataclass Incident, TriageResult, User
                       (slots=True; frozen=True where immutable)
  config.py          — SEVERITY_RULES (ordered list of tuples), SEVERITY_DESCRIPTIONS dict,
                       TEAM_KEYWORDS dict, DEFAULT_TEAM, ESCALATION_POLICY, SEED_USERS, SEED_INCIDENTS
  database.py        — _get_conn(), session() context manager, init_schema(),
                       seed_users(), save_incident(), list_incidents(). NO Flask import.
services/
  __init__.py
  auth_service.py    — find_user_by_username(username) → row dict
                       verify_password(user_row, password) → bool
  severity_service.py — classify_severity(impact, urgency, customer_impact) → (label, description)
  routing_service.py  — route_team(title, description) → str
                        escalation_recommendation(severity) → str
  triage_service.py   — run_triage(...) → result dict. Orchestrates classify → route →
                        handoff → mock. NO Flask import.
integrations/
  __init__.py
  mock_integrator.py — build_mock_payload(...) → dict. NO network I/O.
templates/           — UNCHANGED (same HTML, same field IDs, same button classes)
static/app.js        — UNCHANGED
requirements.txt     — UNCHANGED (Flask>=3.0, Werkzeug>=3.0)

# classify_severity implementation (core/config.py + services/severity_service.py)

SEVERITY_RULES is a priority-ordered list of (label, condition, description) tuples:

    [
      ("P1", {"impact": "high",          "urgency": "*",             "customer_impact": "*"}),
      ("P1", {"impact": "*",             "urgency": "high",          "customer_impact": "yes"}),
      ("P2", {"impact": "medium",        "urgency": "high",          "customer_impact": "*"}),
      ("P3", {"impact": "medium",        "urgency": "*",             "customer_impact": "*"}),
      ("P3", {"impact": "*",             "urgency": "medium",        "customer_impact": "*"}),
      # P4 fallback: no explicit rule needed; return P4 when nothing matched
    ]

A condition value of "*" is a wildcard (matches any input).
Iterate in order; first match returns (label, description).
Fallback: P4 with its description.

# route_team implementation
Lowercase title + " " + description.
For each team: score = number of keywords appearing as substrings in the text.
Return the highest-scoring team. If all scores are 0, return DEFAULT_TEAM.

# JSON API (new)
POST /api/triage  (login required, JSON body):
  Request:  { "title","description","business_area","system_affected",
              "impact_level","urgency","customer_impact" }
  Response 200:
  {
    "incident": { ...echo of the 7 input fields... },
    "severity", "severity_description", "suggested_team",
    "escalation_recommendation", "handoff_summary",
    "mock_payload": { ... }
  }
  Response 400: { "error": "..." }  for missing or malformed JSON body.

# Logging
At the end of each triage (both web and JSON):
  logger.info("Triage: sev=%s team=%s", severity, suggested_team)
Do NOT log raw description text.

# Strict constraints
- NO import of flask in core/ or services/ files.
- NO import of app or router classes in core/ or services/ files.
- app.py does not contain any business logic.
- The template HTML is not modified (form field IDs, button classes, data-* attributes).
- static/app.js is not modified.
- The existing login flow, triage behavior, and result page appear identical.

# Acceptance Criteria (verify before finishing)
  [ ] python app.py starts cleanly
  [ ] /login → operator1 → /triage → Example 1 submits → P1 + API Integration Team
  [ ] /api/triage JSON endpoint works (curl with session cookie or test client)
  [ ] /audit shows the incident
  [ ] No flask import in core/ or services/ (grep -r "import flask" core/ services/ → empty)
  [ ] app.py is < 40 lines
  [ ] 3 auto-fill buttons still work in the browser
  [ ] Admin link still visible only for supervisor
  [ ] /admin still accessible to supervisor1

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. python -m pytest tests/ -v    (will produce 0 tests; that's fine — test suite added in PR #3)
   Confirm the app itself still works per the acceptance checklist above.

2. git show --stat HEAD          (before committing)
   → confirm only the intended files are in the working tree

3. git add .
   git commit -m "refactor: restructure into core/services/integrations architecture"

4. git show --stat HEAD

5. git push -u origin feat/2-refactor

6. gh pr create \
     --base <default-branch> \
     --head feat/2-refactor \
     --title "refactor(2): restructure into production architecture" \
     --body $(cat <<'EOF'
## Summary
Separates HTTP routing (router.py) from business logic (services/) and
configuration (core/). Adds the POST /api/triage JSON endpoint. Adds
domain dataclasses. Removes all Flask imports from core/ and services/.

## What's Changed
- New: core/, services/, integrations/, router.py
- Removed: flat top-level auth.py, db.py, rules.py (if they exist)
- Added: POST /api/triage JSON endpoint
- Added: structured logging (severity + team only, no raw descriptions)
- Templates, static/app.js, requirements.txt: UNCHANGED

## Acceptance Criteria
- [x] App starts on :5000
- [x] Login / triage / result / audit flows work identically to PR #1
- [x] JSON API endpoint returns correct classification
- [x] No flask import in core/ or services/
- [x] app.py < 40 lines
- [x] 3 auto-fill buttons still work
- [x] Admin link visible supervisor-only

## Tests
No test suite yet (introduced in PR #3). Manually verified against
the acceptance checklist.

## Manual Smoke Test
- Logged in as operator1, submitted Example 1, confirmed P1 + API Integration Team.
- Hit /api/triage with curl and confirmed JSON response shape.
- Verified /audit, /admin still work.

## Risk & Rollback
- Risk: medium (behavioral equivalence of refactor not yet proven by tests)
- Rollback: `git revert <merge-commit>` or `gh pr close <n>` and rebase
EOF
)

7. gh pr view

8. STOP. Tell the user:
   "PR #2 is open at [URL]. Please review, approve, and merge it.
   The next prompt begins only after the PR is merged."
```

---

## Prompt 3 — Test Suite

```
Add a comprehensive pytest test suite to the Operational Incident Triage Desk.
Do NOT modify application source files. Only add tests and test infrastructure.

============================================================
STEP 0 — Verify Repository State
============================================================

STOP if any check fails; report to the user and wait for instruction.

1. git remote -v  → must show github.com origin
2. gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'
3. gh pr list --state merged --limit 3
   → most recent must be the refactor PR (PR #2)
4. git status --short  → must be empty
5. git checkout <default-branch> && git pull --ff-only origin <default-branch>
6. Activate the virtual environment and verify dependencies:
     source .venv/bin/activate
     pip list | grep -iE "flask|werkzeug"
   → both packages must be visible. If not, run:  pip install -r requirements.txt
7. git checkout -b feat/3-tests

Only after all steps pass, begin.

============================================================
BEFORE WRITING TESTS — UNDERSTAND THE CODE
============================================================

Read and note:
  core/config.py         — exact SEVERITY_RULES order, TEAM_KEYWORDS, SEED_USERS
  core/database.py       — _get_conn signature, init_schema, seed_users
  services/severity_service.py  — function signature
  services/routing_service.py   — function signature
  router.py              — route names, session key names
  templates/index.html   — form field IDs, button classes, data-* attribute names
  static/app.js          — which IDs it references

This information is required to write correct assertions.

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# Test Infrastructure

Append to requirements.txt:
    pytest>=7.0

pytest.ini  (new file at project root):
    [pytest]
    testpaths = tests
    pythonpath = .
    verbosity = 2
    filterwarnings =
        ignore::DeprecationWarning

tests/__init__.py  (new file, empty)

Shared fixtures — put in tests/conftest.py (new file):

@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    """Temp SQLite DB isolated from developer's incidents.db."""
    db_file = tmp_path_factory.mktemp("triage") / "test.db"
    from core.database import init_schema
    from core.config import SEED_USERS
    init_schema(str(db_file))
    seed_users(SEED_USERS, str(db_file))
    return str(db_file)

@pytest.fixture(autouse=True)
def patch_db(monkeypatch, test_db_path):
    """Force all DB calls to use the temp DB regardless of argument."""
    import core.database as db_mod
    orig = db_mod._get_conn
    monkeypatch.setattr(db_mod, "_get_conn", lambda path=None: orig(test_db_path))
    return test_db_path

@pytest.fixture
def client(test_db_path):
    from app import app
    app.secret_key = "test-secret"
    with app.test_client() as c:
        yield c

# Required Test Files

## tests/test_severity.py
from services.severity_service import classify_severity

P1 (4 cases):
  classify_severity("high",   "low",    "no")  → ("P1", ...)
  classify_severity("high",   "high",   "yes") → ("P1", ...)
  classify_severity("medium", "high",   "yes") → ("P1", ...)
  classify_severity("low",    "high",   "yes") → ("P1", ...)
  Also assert the description contains "Critical"

P2 (1 case):
  classify_severity("medium", "high",   "no")  → ("P2", ...)

P3 (3 cases):
  classify_severity("medium", "low",    "no")  → ("P3", ...)
  classify_severity("medium", "medium", "no")  → ("P3", ...)
  classify_severity("low",    "medium", "no")  → ("P3", ...)

P4 (2 cases):
  classify_severity("low", "low", "no")  → ("P4", ...)
  classify_severity("low", "low", "yes") → ("P4", ...)

Edge cases:
  classify_severity("", "", "")                    → ("P4", ...)
  classify_severity("HIGH", "HIGH", "YES")         → ("P4", ...)   # uppercase doesn't match
  classify_severity("low", "high", "no")           → ("P4", ...)   # no rule matches

## tests/test_routing.py
from services.routing_service import route_team, escalation_recommendation
from core.config import DEFAULT_TEAM

  route_team("API gateway 502 errors", "endpoint down")   → "API Integration Team"
  route_team("ETL pipeline failure", "data warehouse")    → "Data Platform Team"
  route_team("customer billing issue", "account support") → "Customer Operations Team"
  route_team("server disk full", "CPU memory spike")      → "Infrastructure Team"
  route_team("totally unrelated topic", "")               → DEFAULT_TEAM
  escalation_recommendation("P1") → non-empty string
  escalation_recommendation("P4") → non-empty string

## tests/test_auth.py
Using app.test_client() (via client fixture):

  GET /    (no session)       → 302, Location contains /login
  POST /login valid operator  → 302, Location contains /triage
  POST /login invalid creds   → 200 (stays on login page)
  GET /triage (after login)   → 200
  GET /audit  (after login, operator)   → 200
  GET /admin  (after login, operator)   → 302 (denied)
  Log out, log in as supervisor1, GET /admin → 200

Helper:
  def login(client, username="operator1"):
      client.post("/login", data={"username": username, "password": "ChangeMe123!"})

## tests/test_integration.py
  # Unauthenticated
  GET /  (no session) → 302 to /login

  # Web form triage
  login(operator1)
  POST /triage/submit  data={title: "API 502", description: "endpoint errors",
   business_area: "Public Admin", system_affected: "API",
   impact_level: "high", urgency: "high", customer_impact: "yes"}
  follow_redirects → 200, body contains "P1", body contains "API Integration Team"

  # JSON API triage
  login(operator1)
  POST /api/triage json={title:"test", description:"desc", business_area:"ba",
   system_affected:"sa", impact_level:"high", urgency:"medium", customer_impact:"no"}
  → 200, JSON body has keys: severity, severity_description, suggested_team,
    escalation_recommendation, handoff_summary, mock_payload
  assert body["severity"] == "P1"

  # Malformed JSON API
  POST /api/triage json={}  → 400
  POST /api/triage invalid JSON → 400

  # Audit page
  login(operator1), GET /audit → 200, body contains at least one incident title

## tests/test_regression_js_fill.py
  login(operator1)
  resp = client.get("/triage")
  html = resp.data.decode()

  # 3 example buttons exist with class example-btn
  assert html.count('class="example-btn"') >= 3

  # All data-* attributes present on at least one button
  for attr in ["data-title", "data-description", "data-business_area",
               "data-system_affected", "data-impact_level", "data-urgency",
               "data-customer_impact"]:
      assert attr in html, f"Missing data attribute: {attr}"

  # All 7 form field IDs in the rendered form
  for field_id in ["title", "description", "business_area", "system_affected",
                   "impact_level", "urgency", "customer_impact"]:
      assert f'id="{field_id}"' in html, f"Missing form field ID: {field_id}"

  # app.js is loaded
  assert "app.js" in html

============================================================
ACCEPTANCE CRITERIA
============================================================

  [ ] pip install -r requirements.txt  (pytest installs successfully)
  [ ] python -m pytest tests/ -v  passes with 50+ tests, 0 failures
  [ ] No test writes to incidents.db  (verify with: ls -la incidents.db → unchanged size/mtime)
  [ ] python app.py  still starts and works as before
  [ ] No application source files were modified  (git diff --name-only vs main → only tests/* and pytest.ini)

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. python -m pytest tests/ -v
   → record the test count and confirm 0 failures.

2. python app.py  → quick smoke test → Ctrl+C

3. git add .
   git commit -m "test: add full pytest coverage for Incident Triage Desk"

4. git show --stat HEAD
   → confirm only tests/, pytest.ini, requirements.txt are staged

5. git push -u origin feat/3-tests

6. gh pr create \
     --base <default-branch> \
     --head feat/3-tests \
     --title "test(3): add full pytest test suite" \
     --body $(cat <<'EOF'
## Summary
Adds 5 test modules covering severity classification, team routing,
authentication, full integration (web + JSON API), and JS auto-fill
button regression. All tests use an isolated temp SQLite DB.

## What's Changed
- New: tests/ (5 test modules + conftest.py)
- New: pytest.ini
- Modified: requirements.txt (added pytest>=7.0)
- Application source: UNCHANGED

## Acceptance Criteria
- [x] 50+ tests pass
- [x] Severity P1/P2/P3/P4 boundaries covered
- [x] All 4 teams + fallback covered
- [x] Auth: login, logout, role restrictions
- [x] Web form and JSON API integration
- [x] 3 example buttons regression (data attrs + field IDs + app.js)
- [x] Tests isolated from incidents.db

## Tests
Command:  python -m pytest tests/ -v
Results:  <N> passed, 0 failed

## Manual Smoke Test
- Ran `python app.py` after tests; app starts without errors.
- Logged in and submitted an incident; result page correct.

## Risk & Rollback
- Risk: low (tests only; no behavior changes)
- Rollback: unnecessary (no functional change)
EOF
)

7. gh pr view

8. STOP. Tell the user:
   "PR #3 is open at [URL]. Please review, approve, and merge it.
   The next prompt begins only after the PR is merged."
```

---

## Prompt 4 — Governance & P1 Approval Gate

```
Add input validation, PII redaction, a SQLite audit trail, and a
supervisor-approval gate for P1 incidents to the Operational Incident Triage Desk.

============================================================
STEP 0 — Verify Repository State
============================================================

STOP if any check fails; report to the user and wait for instruction.

1. git remote -v
2. gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'
3. gh pr list --state merged --limit 3
   → most recent must be the test suite PR (PR #3)
4. git status --short  → must be empty
5. git checkout <default-branch> && git pull --ff-only origin <default-branch>
6. Activate the virtual environment and verify dependencies:
     source .venv/bin/activate
     pip list | grep -iE "flask|werkzeug"
   → both packages must be visible. If not, run:  pip install -r requirements.txt
7. python -m pytest tests/ -v  → all tests must pass before you begin
8. git checkout -b feat/4-governance

Only after all steps pass, begin.

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# 1. core/gov_config.py  (new file)

ALLOWED_IMPACT_VALUES       = ("low", "medium", "high")
ALLOWED_URGENCY_VALUES      = ("low", "medium", "high")
ALLOWED_CUSTOMER_IMPACT_VAL = ("yes", "no")

MAX_TITLE_LENGTH            = 250
MAX_DESCRIPTION_LENGTH      = 5000
MAX_BUSINESS_AREA_LENGTH    = 150
MAX_SYSTEM_AFFECTED_LENGTH  = 200

P1_APPROVAL_ENABLED         = True

APPROVAL_STATUS_PENDING     = "pending"
APPROVAL_STATUS_APPROVED    = "approved"
APPROVAL_STATUS_DENIED      = "denied"
ALLOWED_RECLASSIFY_TARGETS  = ("P2", "P3", "P4")

# 2. services/validation.py  (new file)

class ValidationError:
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

def validate_incident_input(title, description, business_area,
                            system_affected, impact_level,
                            urgency, customer_impact) -> list[ValidationError]:
    """Returns a list of errors (empty list = valid)."""
    # Checks (in this order):
    #   title non-empty
    #   description non-empty
    #   title length <= MAX_TITLE_LENGTH
    #   description length <= MAX_DESCRIPTION_LENGTH
    #   business_area length <= MAX_BUSINESS_AREA_LENGTH (if truthy)
    #   system_affected length <= MAX_SYSTEM_AFFECTED_LENGTH (if truthy)
    #   impact_level in ALLOWED_IMPACT_VALUES
    #   urgency in ALLOWED_URGENCY_VALUES
    #   customer_impact in ALLOWED_CUSTOMER_IMPACT_VALUES

# 3. core/redactor.py  (new file)

import re
_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                       "[SSN REDACTED]"),
    (re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),      "[PHONE REDACTED]"),
    (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[CARD REDACTED]"),
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[EMAIL REDACTED]"),
]

def redact(text: str) -> str:
    """Replace PII patterns with markers. Never raises."""
    if not text: return ""
    result = str(text)
    for pattern, marker in _PATTERNS:
        result = pattern.sub(marker, result)
    return result

# 4. Database schema migration (add to core/database.py)

Add to SCHEMA_SQL (or add a MIGRATION_SQL executed in init_schema):
    ALTER TABLE incidents ADD COLUMN status         TEXT    NOT NULL DEFAULT 'approved';
    ALTER TABLE incidents ADD COLUMN severity_level INTEGER NOT NULL DEFAULT 4;

Note: use try/except so this works on both fresh and existing DBs.

Ensure the incidents table has the status column (default 'approved').

Add new database functions (add to core/database.py):

  severity_to_level(label: str) -> int
    # P1→1, P2→2, P3→3, P4→4; fallback 4

  get_by_id(incident_id: int, db_path=None) -> dict | None
  get_pending_p1s(db_path=None) -> list[sqlite3.Row]
    # WHERE severity='P1' AND status='pending' ORDER BY created_at DESC
  get_all_filtered_by(status=None, severity=None, db_path=None) -> list[sqlite3.Row]
  approve(incident_id, reason=None, db_path=None)
    # UPDATE incidents SET status='approved' WHERE id=? AND status='pending'
  deny(incident_id, reason, db_path=None)
    # UPDATE incidents SET status='denied' WHERE id=? AND status='pending'
  reclassify(incident_id, new_severity, db_path=None)
    # UPDATE incidents SET severity=?, severity_level=?, status='approved'
    #   WHERE id=? AND severity='P1' AND status='pending'
  update_pending(incident_id, title, description, business_area,
                 system_affected, impact_level, urgency, customer_impact, db_path=None)
  save_audit_log(entry: dict, db_path=None)
    # INSERT INTO audit_log (username, role, incident_id, severity, team, action, reason)
  list_audit_log(limit=50, db_path=None) -> list[sqlite3.Row]
    # ORDER BY timestamp DESC

  Ensure audit_log table exists (add to SCHEMA_SQL if not present):
    CREATE TABLE IF NOT EXISTS audit_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT NOT NULL DEFAULT (datetime('now')),
      username TEXT NOT NULL,
      role TEXT NOT NULL,
      incident_id INTEGER,
      severity TEXT,
      team TEXT,
      action TEXT NOT NULL,
      reason TEXT
    );

# 5. P1 approval gate (router.py and/or triage_service.py)

In the triage submission handler (both /triage/submit and /api/triage):

  severity, _ = classify_severity(impact_level, urgency, customer_impact)
  if severity == "P1" and session.get("role") != "supervisor" and P1_APPROVAL_ENABLED:
      approval_status = "pending"
  else:
      approval_status = "approved"

  # Pass approval_status to save_incident so the DB row is correct

Add to the result context:
  result["requires_approval"] = (approval_status == "pending")

# 6. Result page UI change (templates/result.html)

If result.get("requires_approval"):
  Show a yellow/amber banner ABOVE the details:
  "⚠ This P1 incident requires supervisor approval before escalation steps may proceed.
   Current status: PENDING APPROVAL"

When NOT requires_approval, no banner needed.

# 7. Policy banner (if not already in templates)
Add to templates/index.html AND templates/result.html:
  <div class="policy-banner">
    This tool is for internal decision support. Final ownership remains with human operators.
  </div>

# 8. Audit route (router.py + templates/audit.html)
GET /audit  (login required, any role):
  Show two sections:
  1. "Recent Incidents" — list_incidents() → table: id, title, severity, team, submitter, status, created_at
  2. "Audit Log"        — list_audit_log() → table: time, user, role, incident_id, action, reason

# 9. New tests — add tests/test_governance.py

## Validation
  validate_incident_input("", "desc", "ba", "sa", "low", "low", "no") → 1 error (title)
  validate_incident_input("t", "", "ba", "sa", "low", "low", "no")   → 1 error (description)
  validate_incident_input("t", "d", "ba", "sa", "CRITICAL", "low", "no") → 1 error (impact)
  validate_incident_input("t", "d", "ba", "sa", "low", "low", "no") → [] (valid)
  "x" * 251 as title → 1 error (length)

## Redaction
  redact("Contact john.doe@example.com")     → contains "[EMAIL REDACTED]"
  redact("SSN: 123-45-6789 on file")         → contains "[SSN REDACTED]"
  redact("Call (555) 123-4567")              → contains "[PHONE REDACTED]"
  redact("Card 4111 1111 1111 1111")         → contains "[CARD REDACTED]"
  redact("")                                 → ""
  redact("no pii here")                      → "no pii here" (unchanged)

## P1 approval gate (integration via app.test_client())
  login(operator1)
  POST /triage/submit with P1 fields (high/medium/yes)
  → result page shows "requires_approval" or "PENDING APPROVAL" text

  Login as supervisor1
  POST /triage/submit with same P1 fields
  → result page does NOT show pending banner (auto-approved)

## Audit log
  After submitting an incident, GET /audit → page contains the incident title
  GET /audit → page contains "audit" log section (or audit entries visible)

## Existing tests
  Run full suite: python -m pytest tests/ -v
  → all PR#1–3 tests must still pass (no regressions)

============================================================
ACCEPTANCE CRITERIA
============================================================

  [ ] python -m pytest tests/ -v  → all tests pass (old + new)
  [ ] operator1 submits P1  → "PENDING APPROVAL" banner visible
  [ ] supervisor1 submits P1 → no pending banner (auto-approved)
  [ ] /audit shows incident list AND audit log entries
  [ ] redact() catches all 4 PII patterns
  [ ] Validation returns errors for empty title, invalid impact value, over-length title
  [ ] policy banner visible on triage + result pages
  [ ] python app.py  → app starts cleanly, full flow works
  [ ] No flask import added to core/ or services/

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. python -m pytest tests/ -v
   → ALL tests must pass. Record the count.

2. python app.py
   → Operator P1 → pending banner; Supervisor P1 → approved; /audit shows log.
   → Ctrl+C to stop.

3. git add .
   git commit -m "feat(4): add governance, P1 approval gate, PII redaction, audit trail"

4. git show --stat HEAD

5. git push -u origin feat/4-governance

6. gh pr create \
     --base <default-branch> \
     --head feat/4-governance \
     --title "feat(4): governance, P1 approval gate, PII redaction, audit trail" \
     --body $(cat <<'EOF'
## Summary
Adds input validation, PII redaction in logs, a SQLite audit trail, and a
supervisor-approval gate for P1 incidents. Operator P1s are stored as
"pending"; supervisor P1s are auto-approved.

## What's Changed
- New: core/gov_config.py, services/validation.py, core/redactor.py
- Modified: core/database.py (audit_log table, status column, new query functions)
- Modified: router.py (validation on submit, P1 gate logic, audit log entries)
- Modified: templates/result.html (pending banner), templates/audit.html (audit log section)
- New: tests/test_governance.py

## Acceptance Criteria
- [x] Operator P1 → "PENDING APPROVAL" banner
- [x] Supervisor P1 → auto-approved, no banner
- [x] PII: email, phone, SSN, and card all redacted
- [x] Validation: empty fields, invalid values, over-length fields
- [x] Audit trail rows created on each submission
- [x] /audit shows incidents + audit log
- [x] All existing tests still pass

## Tests
Command:  python -m pytest tests/ -v
Results:  <N> passed, 0 failed  (existing + new)

## Manual Smoke Test
- Submitted P1 as operator1 → saw pending banner.
- Submitted P1 as supervisor1 → approved, no banner.
- Checked /audit → saw incident and audit log rows.

## Risk & Rollback
- Risk: low (governance only; no breaking changes to existing flows)
- Rollback: `gh pr close <n>` — revert is clean since changes are additive
EOF
)

7. gh pr view

8. STOP. Tell the user:
   "PR #4 is open at [URL]. Please review, approve, and merge it.
   The next prompt begins only after the PR is merged."
```

---

## Prompt 5 — Supervisor Admin Workflow

```
Add the full supervisor admin dashboard to the Operational Incident Triage Desk:
approve, deny, reclassify, and edit pending P1 incidents. All actions are
audit-logged. The operator role cannot access any /admin route.

============================================================
STEP 0 — Verify Repository State
============================================================

STOP if any check fails; report to the user and wait for instruction.

1. git remote -v
2. gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'
3. gh pr list --state merged --limit 3
   → most recent must be the governance PR (PR #4)
4. git status --short  → must be empty
5. git checkout <default-branch> && git pull --ff-only origin <default-branch>
6. Activate the virtual environment and verify dependencies:
     source .venv/bin/activate
     pip list | grep -iE "flask|werkzeug"
   → both packages must be visible. If not, run:  pip install -r requirements.txt
7. python -m pytest tests/ -v  → all tests must pass before starting
8. git checkout -b feat/5-admin

Only after all steps pass, begin.

============================================================
BEFORE WRITING CODE — CHECK WHAT EXISTS
============================================================

Read router.py and core/database.py to confirm:
  ✅ get_by_id, get_pending_p1s, get_all_filtered_by exist
  ✅ approve, deny, reclassify, update_pending exist
  ✅ save_audit_log, list_audit_log exist
  ✅ severity_to_level exists
  ✅ validate_incident_input exists

If any function is missing, add it first before writing the routes.

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# Route Summary

  GET  /admin                          → supervisor-only dashboard
  POST /admin/approve                  → approve a pending P1
  POST /admin/deny                     → deny a pending P1 (reason required)
  POST /admin/reclassify               → reclassify P1 to P2/P3/P4 (reason required)
  GET  /admin/edit/<int:incident_id>   → edit form for pending P1
  POST /admin/edit/<int:incident_id>   → save edits, re-run classification

All /admin routes require supervisor role (use the existing role_required decorator).

# 1. Admin Dashboard (GET /admin)

Fetch and render four lists:
  pending_p1s      = get_pending_p1s()
  approved_p1s     = get_all_filtered_by(status="approved",    severity="P1")
  denied_p1s       = get_all_filtered_by(status="denied",      severity="P1")
  reclassified_p1s = get_all_filtered_by(severity != "P1")     # any non-P1 that was reclassified
                       (or: incidents WHERE reclassified flag is set — use status if simpler)

Render in templates/admin.html with four sections, each showing:
  count badge, then a table/list of incidents.

Each incident row:
  Incident ID · Title (truncated to 40 chars) · Severity · Team ·
  Submitter · Submitted at · Status · Approver/Reason (if applicable)

For pending P1s, show action buttons in the row:
  [Approve]  [Deny]  [Reclassify]  [Edit]

# 2. POST /admin/approve  (supervisor only)

Input (form or JSON): incident_id (int, required)

Logic:
  incident = get_by_id(incident_id)
  if not incident:
      flash("Incident not found.", "danger"); redirect to /admin
  if incident["severity"] != "P1" or incident["status"] != "pending":
      flash("Only pending P1 incidents can be approved.", "warning"); redirect to /admin
  approve(incident_id)
  save_audit_log({
      "username": session["username"],
      "role": "supervisor",
      "incident_id": incident_id,
      "severity": "P1",
      "team": incident["suggested_team"],
      "action": "approved",
      "reason": "Approved by supervisor"
  })
  flash(f"Incident #{incident_id} approved.", "success")
  redirect to /admin

# 3. POST /admin/deny  (supervisor only)

Input: incident_id (int, required), reason (string, REQUIRED)

Logic:
  if not reason:
      flash("A denial reason is required.", "danger"); redirect to /admin
  incident = get_by_id(...)  → same guards as approve
  deny(incident_id, reason)
  save_audit_log({ ..., "action": "denied", "reason": reason })
  flash(f"Incident #{incident_id} denied.", "success")
  redirect to /admin

# 4. POST /admin/reclassify  (supervisor only)

Input: incident_id (int, required), new_severity (str, in ("P2","P3","P4")),
       reason (string, REQUIRED)

Logic:
  if new_severity not in ALLOWED_RECLASSIFY_TARGETS:
      flash(f"Target must be one of: {', '.join(ALLOWED_RECLASSIFY_TARGETS)}", "danger")
      redirect
  if not reason:
      flash("A reclassification reason is required.", "danger"); redirect
  incident = get_by_id(...) → same guards
  reclassify(incident_id, new_severity)
  save_audit_log({ ..., "action": "reclassified", "severity": new_severity, "reason": reason })
  flash(f"Incident #{incident_id} reclassified to {new_severity}.", "success")
  redirect to /admin

# 5. Edit Pending P1 — GET /admin/edit/<int:incident_id>

  incident = get_by_id(incident_id)
  if not incident or incident["status"] != "pending" or incident["severity"] != "P1":
      flash("Only pending P1 incidents can be edited.", "warning"); redirect to /admin

  Render admin.html with the edit_incident variable set to the incident dict.
  The admin template should show an inline edit form pre-filled with the
  incident's current values when edit_incident is not None.

# 6. Edit Pending P1 — POST /admin/edit/<int:incident_id>

  # 6a. Validate
  errors = validate_incident_input(title, description, business_area,
                                    system_affected, impact_level, urgency, customer_impact)
  if errors: flash each; re-render edit form

  # 6b. Guard
  incident = get_by_id(incident_id)
  if not incident or incident["status"] != "pending":
      flash("Only pending incidents can be edited.", "warning"); redirect to /admin

  # 6c. Save editable fields
  update_pending(incident_id, title, description, business_area,
                 system_affected, impact_level, urgency, customer_impact)

  # 6d. Re-run classification
  new_severity, new_sev_desc = classify_severity(impact_level, urgency, customer_impact)
  new_team = route_team(title, description)
  new_escalation = escalation_recommendation(new_severity)
  new_handoff = build_handoff_summary(title, business_area, system_affected,
                                        impact_level, urgency, customer_impact,
                                        new_severity, new_sev_desc, new_team)
  new_level = severity_to_level(new_severity)

  # 6e. Update classification fields in DB
  with db_session() as conn:
      conn.execute(
          "UPDATE incidents SET severity=?, severity_description=?, suggested_team=?,"
          " escalation_recommendation=?, handoff_summary=?, severity_level=?"
          " WHERE id=? AND status='pending'",
          (new_severity, new_sev_desc, new_team, new_escalation, new_handoff,new_level, incident_id)
      )

  # 6f. Audit
  action = "reclassified" if new_severity != "P1" else "edited"
  save_audit_log({
      "username": session["username"], "role": "supervisor",
      "incident_id": incident_id, "severity": new_severity,
      "team": new_team, "action": action,
      "reason": f"Edited by supervisor → {new_severity} / {new_team}"
  })

  flash(f"Incident #{incident_id} updated. New severity: {new_severity}.", "success")
  redirect to /admin

# 7. templates/admin.html

Structure (keep consistent with the existing UI style):
  - Navbar (same as other pages, Admin link active)
  - Policy banner
  - Flash messages
  - <h1>Supervisor Dashboard</h1>
  - Four sections:
      Pending P1 (amber)        — table + action buttons
      Approved P1 (green)       — read-only table
      Denied P1 (red)           — read-only table with reason
      Reclassified (grey)       — read-only table with old→new severity
  - If edit_incident is set, show an edit form card at the top with:
      title, description, business_area, system_affected,
      impact_level, urgency, customer_impact
      [Save Changes] button

Action buttons for pending P1s (small inline form):
  <form method="POST" action="{{ url_for('admin_approve') }}">
    <input type="hidden" name="incident_id" value="{{ incident['id'] }}">
    <button type="submit">Approve</button>
  </form>
  ... similarly for deny and reclassify (with a reason input and severity select)
  <a href="{{ url_for('admin_edit_get', incident_id=incident['id']) }}">Edit</a>

# 8. New tests — tests/test_admin.py

## Fixtures (mirror the pattern from tests/test_integration.py)

@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    ... (same as other test files)

@pytest.fixture(autouse=True)
def patch_db(monkeypatch, test_db_path):
    ... (same)

@pytest.fixture
def client(test_db_path):
    ... (same)

def login_as(client, role="operator"):
    username = "operator1" if role == "operator" else "supervisor1"
    client.post("/login", data={"username": username,
                                "password": "ChangeMe123!"})

def submit_p1(client):
    """Submit a P1 incident as operator1 and return the incident ID from the DB."""
    client.post("/triage/submit", data={
        "title": "P1 Test Incident",
        "description": "Critical API 502 errors affecting all customers",
        "business_area": "Public Administration",
        "system_affected": "Core API",
        "impact_level": "high", "urgency": "high", "customer_impact": "yes",
    })
    import core.database as db
    with db.session() as conn:
        row = conn.execute(
            "SELECT id FROM incidents WHERE title='P1 Test Incident' ORDER BY id DESC"
        ).fetchone()
    return row["id"]

## Auth tests
  login_as(client, "operator"); GET /admin → 302
  login_as(client, "supervisor"); GET /admin → 200

## Approve
  incident_id = submit_p1(client)
  login_as(client, "supervisor")
  POST /admin/approve  data={"incident_id": str(incident_id)}
  → redirect to /admin
  GET /admin → page shows "approved" for that incident
  # audit check
  import core.database as db
  with db.session() as conn:
      entries = conn.execute(
          'SELECT * FROM audit_log WHERE incident_id=?', (incident_id,)
      ).fetchall()
  assert len(entries) >= 1

## Deny — missing reason
  incident_id = submit_p1(client); login_as(supervisor)
  POST /admin/deny  data={"incident_id": str(incident_id)}  (no reason)
  → redirect, flash contains "reason"

## Deny — valid
  POST /admin/deny  data={"incident_id": ..., "reason": "Duplicate"}
  → redirect, incident status=denied in DB

## Reclassify — invalid target
  POST /admin/reclassify  data={"incident_id":..., "new_severity":"P9", "reason":"x"}
  → redirect, flash contains "must be one of" or similar

## Reclassify — valid P1→P3
  POST /admin/reclassify  data={"incident_id":..., "new_severity":"P3", "reason":"Lower risk"}
  → redirect, incident severity=P3, status=approved in DB

## Edit — keep P1
  incident_id = submit_p1(client); login_as(supervisor)
  GET /admin/edit/<id> → 200, page contains edit form
  POST /admin/edit/<id>  data={title:"Updated title", description:"still critical API errors",
    business_area:"Public Admin", system_affected:"Core API",
    impact_level:"high", urgency:"high", customer_impact:"yes"}
  → redirect, incident still P1, title updated

## Edit — severity drops
  POST /admin/edit/<id>  data={title:"Low issue", description:"minor disk warning",
    business_area:"IT", system_affected:"Disk",
    impact_level:"low", urgency:"low", customer_impact:"no"}
  → redirect, incident severity=P4 (or P3 depending on rules), title updated

## Edit — blocked for non-pending
  Approve the incident first, then try to edit → redirect with warning flash

## JS regression (in admin template or index)
  login_as(operator); GET /triage → page still has 3 example-btn buttons

============================================================
ACCEPTANCE CRITERIA (automated)
============================================================

  [ ] python -m pytest tests/ -v  → ALL tests pass (existing + new)
  [ ] Operator cannot access /admin (302)
  [ ] Supervisor sees pending/approved/denied sections on /admin
  [ ] Approve: pending → approved, audit logged
  [ ] Deny: pending → denied, reason stored, audit logged
  [ ] Reclassify P1→P3: severity changes, status=approved, audit logged
  [ ] Reclassify invalid target rejected
  [ ] Edit: fields updated, classification re-run, audit logged
  [ ] Edit severity-drop: severity and status both updated
  [ ] Edit blocked for non-pending incidents
  [ ] 3 example buttons still work on /triage

============================================================
ACCEPTANCE CRITERIA (manual smoke test — do this before committing)
============================================================

  python app.py

  1. Log in as operator1. Submit "Public Admin: Benefits API 502" example → P1, pending banner.
  2. Log in as supervisor1. Go to /admin. See the incident in "Pending P1".
  3. Click Approve. Refresh /admin. Incident moves to "Approved P1".
  4. Log in as operator1 again. Submit another P1. → pending.
  5. Log in as supervisor1. Go to /admin. Reclassify it to P3.
     → It appears in "Reclassified".
  6. Submit a third P1 as operator1. Go to /admin/edit/<id>.
     Change impact to "low" and urgency to "low". Save.
     → New severity is P4. Incident no longer in "Pending P1".
  7. Go to /audit. All actions visible in the audit log.

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. python -m pytest tests/ -v
   → ALL tests pass. Record count.

2. python app.py
   → Run the manual smoke test checklist above. Ctrl+C to stop.

3. git add .
   git commit -m "feat(5): add supervisor admin workflow — approve, deny, reclassify, edit"

4. git show --stat HEAD

5. git push -u origin feat/5-admin

6. gh pr create \
     --base <default-branch> \
     --head feat/5-admin \
     --title "feat(5): supervisor admin workflow" \
     --body $(cat <<'EOF'
## Summary
Implements the full supervisor admin dashboard: view pending/approved/denied
and reclassified P1 incidents, approve, deny (with reason), reclassify
(P1→P2/P3/P4 with reason), and edit pending P1 submissions with
automatic re-classification on save. All actions audit-logged.

## What's Changed
- Modified: router.py (6 new admin routes)
- Modified: templates/admin.html (full dashboard + edit form)
- New: tests/test_admin.py
- Application behavior for non-admin users: UNCHANGED

## Acceptance Criteria
- [x] Operator blocked from /admin
- [x] Supervisor sees 4 sections on /admin
- [x] Approve, Deny, Reclassify all work and audit-log
- [x] Reclassify to invalid target is rejected
- [x] Deny and Reclassify require a reason
- [x] Edit updates fields and re-runs classification
- [x] Edit severity-drop: severity and status both updated
- [x] Edit blocked for non-pending incidents
- [x] 3 auto-fill buttons still work

## Tests
Command:  python -m pytest tests/ -v
Results:  <N> passed, 0 failed  (all existing + 20+ new admin tests)

## Manual Smoke Test
- Full operator → pending → supervisor approve / deny / reclassify /
  edit workflow exercised in the running app (see PR acceptance checklist).

## Risk & Rollback
- Risk: low (additive routes only; existing flows unchanged)
- Rollback: `gh pr close <n>` — no migration conflicts
EOF
)

7. gh pr view

8. STOP. Tell the user:
   "PR #5 is open at [URL]. Please review, approve, and merge it.
   The next prompt begins only after the PR is merged."
```

---

## Prompt 6 — Documentation & Final Polish (Optional)

```
Complete the Operational Incident Triage Desk with architecture documentation,
a smoke test, and final cleanup. This is the closing prompt — after it the
project is shippable.

============================================================
STEP 0 — Verify Repository State
============================================================

STOP if any check fails; report to the user and wait for instruction.

1. git remote -v
2. gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'
3. gh pr list --state merged --limit 3
   → most recent must be the admin workflow PR (PR #5)
4. git status --short  → must be empty
5. git checkout <default-branch> && git pull --ff-only origin <default-branch>
6. Activate the virtual environment and verify dependencies:
     source .venv/bin/activate
     pip list | grep -iE "flask|werkzeug"
   → both packages must be visible. If not, run:  pip install -r requirements.txt
7. python -m pytest tests/ -v  → all tests must pass
8. git checkout -b feat/6-polish

============================================================
STEP 1 — IMPLEMENTATION
============================================================

# 1. ARCHITECTURE.md  (new file at project root)

Write a clear, concise document (200–400 lines) covering:

## Components
One paragraph per component, with a small tree diagram:
  app.py, router.py, core/, services/, integrations/, templates/, tests/

## Request Flows
For each flow below, show a numbered step sequence (no code needed, just
"1. router parses… 2. service classifies… 3. database saves…"):
  1. Login
  2. Web triage submission (form → validate → classify → route → persist → audit → render)
  3. JSON API (/api/triage)
  4. P1 approval gate decision point
  5. Admin: approve
  6. Admin: deny
  7. Admin: reclassify
  8. Admin: edit with re-classification

## Severity & Routing Logic
Reproduce the severity rule table (6 rows) and the team keyword dict
(4 teams, all keywords listed).

## Governance
- Validation rules and limits (from gov_config.py)
- PII redaction patterns
- Audit log schema (table columns)
- P1 approval state machine: pending → approved | denied | reclassified

## Mock Integration
What the payload contains, what it does NOT do (no network I/O),
where it is displayed.

## Design Decisions & Tradeoffs
- Flat Python config over YAML/TOML (reason: demo scope, no parser dependency)
- SQLite over PostgreSQL (reason: zero-config, local, single-process)
- No CSRF tokens (reason: demo scope; note as a production risk)
- Jinja inline CSS (reason: no build step, no CDN dependency)
- No external services (reason: self-contained demo)

# 2. tests/test_smoke.py  (new file)

One end-to-end test function that exercises the full operator → supervisor
workflow without helper functions (self-contained):

def test_full_operator_to_supervisor_workflow(client, test_db_path):
    # Step 1: operator submits a P1
    client.post("/login", data={"username":"operator1", "password":"ChangeMe123!"})
    client.post("/triage/submit", data={
        "title":"Smoke Test P1","description":"API integration 502 errors affecting all customers",
        "business_area":"Public Admin","system_affected":"Core API",
        "impact_level":"high","urgency":"high","customer_impact":"yes"})

    # Step 2: supervisor approves it
    client.post("/logout")
    client.post("/login", data={"username":"supervisor1", "password":"ChangeMe123!"})
    resp = client.get("/admin")
    assert b"Smoke Test P1" in resp.data

    # Step 3: find its ID
    import core.database as db
    with db.session() as conn:
        row = conn.execute(
            'SELECT id FROM incidents WHERE title="Smoke Test P1" ORDER BY id DESC LIMIT 1'
        ).fetchone()
    incident_id = row["id"]

    # Step 4: approve
    client.post("/admin/approve", data={"incident_id":str(incident_id)})

    # Step 5: verify status
    with db.session() as conn:
        row = conn.execute(
            'SELECT status FROM incidents WHERE id=?',(incident_id,)).fetchone()
    assert row["status"] == "approved"

    # Step 6: audit log has the entry
    with db.session() as conn:
        entries = conn.execute(
            'SELECT * FROM audit_log WHERE incident_id=?',(incident_id,)).fetchall()
    assert len(entries) >= 1

# 3. Update run_tests.sh  (new or rewrite)
  #!/usr/bin/env bash
  set -eo pipefail
  echo "=== Installing test dependencies ==="
  pip install -r requirements.txt -q
  echo "=== Running full test suite ==="
  python -m pytest tests/ -v
  echo "=== PASS ==="

# 4. .gitignore  (verify and add any missing entries)
  incidents.db
  __pycache__/
  *.pyc
  *.pyo
  .pytest_cache/
  .venv/
  venv/
  .aider/
  .opencode/

# 5. Clean up
  Remove any unused imports (run: python -m py_compile app.py router.py 2>&1 or a quick grep)
  Confirm requirements.txt has exactly: Flask>=3.0, Werkzeug>=3.0, pytest>=7.0
  No TODO/FIXME comments left in source

# 6. Update README.md
  Ensure it has:
    - Project name and one-line description
    - Quick start (install + run commands)
    - Seeded users table
    - Feature list (bullet points)
    - Architecture tree (short)
    - How to run tests
    - Limitations section
    - How to use the admin workflow (operator vs supervisor steps)

============================================================
ACCEPTANCE CRITERIA
============================================================

  [ ] python -m pytest tests/ -v  → ALL tests pass including test_smoke.py
  [ ] ARCHITECTURE.md exists and covers all 6 sections listed above
  [ ] run_tests.sh is executable and passes
  [ ] README.md is complete
  [ ] .gitignore covers all runtime artifacts
  [ ] python app.py  → starts cleanly; full operator→supervisor flow works
  [ ] No unused imports in app.py, router.py, core/, services/

============================================================
FINAL STEPS
============================================================

Ensure the venv is active before running any Python command:
     source .venv/bin/activate

1. python -m pytest tests/ -v
   → ALL tests pass. Record count.

2. bash run_tests.sh
   → PASS

3. python app.py
   → Full workflow smoke test
   → Ctrl+C

4. git add .
   git commit -m "docs(6): add architecture doc, smoke test, final polish"

5. git show --stat HEAD

6. git push -u origin feat/6-polish

7. gh pr create \
     --base <default-branch> \
     --head feat/6-polish \
     --title "docs(6): architecture documentation and project closeout" \
     --body $(cat <<'EOF'
## Summary
Final documentation pass: ARCHITECTURE.md, end-to-end smoke test,
run_tests.sh helper, .gitignore hardening, README cleanup.
The project is now complete and shippable.

## What's Changed
- New: ARCHITECTURE.md, tests/test_smoke.py, run_tests.sh
- Updated: .gitignore, README.md

## Acceptance Criteria
- [x] All tests pass (including new smoke test)
- [x] ARCHITECTURE.md covers all required sections
- [x] README.md is complete and accurate
- [x] run_tests.sh works
- [x] App starts and full workflow works

## Tests
Command:  python -m pytest tests/ -v
Results:  <N> passed, 0 failed

## Manual Smoke Test
- Full operator → pending → supervisor approve workflow verified in running app.

## Risk & Rollback
- Risk: none (docs and tests only)
EOF
)

8. gh pr view

9. STOP. Tell the user:
   "PR #6 is open at [URL]. This is the final PR.
    Please review, approve, and merge it.
    Once merged, the project is complete."

   After the merge, you can verify with:
     gh pr list --state merged
   All 6 PRs should show as merged.

   To run the finished product:
     pip install -r requirements.txt
     python app.py
     # → http://localhost:5000   (logins in README.md)

   To run the full test suite:
     bash run_tests.sh
```

---

## Appendix — Complete Workflow Sequence

```
Prompt 1   →  feat/1-prototype  →  PR #1  →  [HUMAN: review, approve, merge]
Prompt 2   →  feat/2-refactor   →  PR #2  →  [HUMAN: review, approve, merge]
Prompt 3   →  feat/3-tests      →  PR #3  →  [HUMAN: review, approve, merge]
Prompt 4   →  feat/4-governance →  PR #4  →  [HUMAN: review, approve, merge]
Prompt 5   →  feat/5-admin      →  PR #5  →  [HUMAN: review, approve, merge]
Prompt 6   →  feat/6-polish     →  PR #6  →  [HUMAN: review, approve, merge]
                                                     ↓
                                                PROJECT COMPLETE
```

Human terminal commands between prompts (optional shortcuts):

```bash
# View the open PR
gh pr view

# Approve
gh pr review <n> --approve

# Merge (squash)
gh pr merge <n> --squash

# Verify it's merged
gh pr list --state merged --limit 1
```
