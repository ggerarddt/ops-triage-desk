---
name: bugfix-pr
description: Diagnose a bug from a short report or manual reproduction, protect the failure with a regression test, implement a focused fix, verify locally, and open a GitHub pull request without merging it.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: automation
---

# Bugfix PR Workflow

You are operating inside a GitHub repository. The user may provide only a plain-language description of what is not working. Treat that as enough to start: inspect the repo, reproduce the failure where practical, identify the root cause, write or update tests, fix the issue, verify, push, and open a PR.

Use `git` and `gh` as the source of truth for repository state. Do not merge the PR.

## Start Safely

1. Inspect the repository:
   - `git status --short`
   - `git branch --show-current`
   - `git remote -v`
   - `gh repo view --json nameWithOwner,defaultBranchRef`
   - `gh pr list --state open --limit 20`

2. Protect existing work:
   - Do not overwrite, revert, or reformat unrelated user changes.
   - If the worktree has unrelated changes, leave them alone.
   - If unrelated changes block the fix, explain the conflict and ask how to proceed.

3. Start from the latest default branch:
   - Determine the default branch from GitHub, usually `master` or `main`.
   - Check out the default branch.
   - Pull the latest code from origin.
   - Create a dedicated branch named `fix/<short-bug-slug>`.
   - If the user provided an issue number, include it in the branch name: `fix/<issue-number>-<short-bug-slug>`.

## Understand The Bug

4. Normalize the bug report:
   - Restate the expected behavior.
   - Restate the actual behavior.
   - Capture reproduction steps.
   - Infer missing details from the application and tests before asking the user.
   - Ask a question only when the bug cannot be reproduced or scoped without a risky assumption.

5. Diagnose before editing:
   - Search the codebase for relevant routes, components, templates, scripts, tests, and recent changes.
   - Reproduce the failure with the smallest practical command, unit test, integration test, browser check, or manual smoke test.
   - Identify the likely root cause before changing production code.
   - Keep notes for the PR body.

## Test First, Or As Close As Practical

6. Add or update a regression test:
   - Prefer the smallest automated test that fails on the current bug and passes after the fix.
   - For backend bugs, test the service, route, API, or persistence layer closest to the failure.
   - For frontend/template bugs, test rendered markup, static script wiring, DOM ids/names, and any available browser-facing behavior.
   - If a true failing test cannot be written before the fix, explain why and add the best protective test immediately after the fix.

7. Confirm the regression:
   - Run the targeted test.
   - Confirm it fails for the expected reason before or during the fix, unless a pre-fix failing test is impractical.

## Fix Narrowly

8. Implement the fix:
   - Fix the root cause, not only the visible symptom.
   - Keep the diff focused on the bug.
   - Avoid unrelated refactors, formatting churn, dependency changes, or broad rewrites.
   - Preserve public behavior and APIs unless the bug requires a deliberate change.
   - Update documentation only when the fix changes expected behavior or setup.

## UI Bug Checklist

For UI bugs, including one-click example buttons, do all applicable checks:

- Confirm buttons that should only populate fields use `type="button"` or otherwise do not submit the form accidentally.
- Confirm JavaScript files are loaded by the rendered template.
- Confirm event listeners attach after the target elements exist.
- Confirm field ids, names, and selectors match the script.
- Confirm each example includes data for every required form field.
- Confirm clicking each example populates every expected field.
- Verify in a browser when practical; otherwise add a DOM/rendered-template regression test that would catch broken wiring.

## Verify

9. Run checks:
   - Run the targeted regression test.
   - Run the relevant test suite.
   - Run the full test suite when practical.
   - Run lint, typecheck, build, or smoke-test commands discovered in README, AGENTS.md, package scripts, Makefile, pyproject, tox, CI config, or similar project files.
   - If a check cannot be run, record the reason in the PR body.

10. Inspect the final diff:
    - `git diff`
    - `git status --short`
    - Ensure only intended files changed.
    - Ensure no secrets, local database files, logs, build artifacts, or unrelated generated files are included.

## Issue Handling

11. Use an issue only when appropriate:
    - If the user provided an issue number, reference it.
    - If the repository workflow clearly expects issues, create one with `gh issue create`.
    - If the bug is small and the user did not ask for an issue, opening only a PR is acceptable.
    - Do not let issue creation block the bugfix if the PR can clearly describe the problem.

## Commit And PR

12. Commit:
    - Use conventional commit format: `fix: <short description>`.
    - Include the issue reference in the body when an issue exists.
    - Do not include unrelated changes in the commit.

13. Push and open a PR:
    - Push the branch to origin.
    - Open a PR with `gh pr create`.
    - Target the repository default branch.
    - Do not merge the PR.

14. PR body must include:
    - Summary
    - Root cause
    - Reproduction
    - Fix
    - Tests run
    - Manual verification, if any
    - Risk and rollback
    - `Closes #<issue-number>` only when an issue exists

## Stop Condition

After opening the PR:

- Report the PR URL.
- Summarize the fix and tests.
- Stop. Human review and merge are required gates.
