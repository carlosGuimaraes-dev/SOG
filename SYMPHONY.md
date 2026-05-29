---
symphony:
  version: 1
  mode: initiative-plus-execution

tracker:
  kind: linear
  project_slug: "sog-19e506c6c308"
  active_states:
    - Todo
    - In Progress
  terminal_states:
    - Done
    - Closed
    - Cancelled
    - Canceled
    - Duplicate
  export:
    parent_issue: true
    child_issues: true
    afk_state: Todo
    hitl_state: Backlog

initiative:
  root: .symphony/initiatives
  default_pipeline:
    - elicit
    - diagnose
    - prd
    - issues
    - review
    - approve
    - handoff
    - export
  required_artifacts:
    - initiative.yml
    - initiative.md
    - diagnosis.md
    - prd.md
    - issues.draft.md
    - review.md
    - issues.approved.md
    - handoff.md
    - export.json
  hitl:
    required_before_export: true
    export_after_approval: true

workspace:
  root: ~/code/symphony-workspaces
  issue_path: "{{ issue.identifier }}"

hooks:
  after_create: |
    git clone --depth 1 git@github.com:carlosGuimaraes-dev/SOG.git .
    if [ -f .env.example ] && [ ! -f .env ]; then
      cp .env.example .env
    fi
    if command -v python3 >/dev/null 2>&1; then
      python3 -m venv .venv || true
      . .venv/bin/activate
      pip install -r agente/requirements.txt -r agente/requirements-dev.txt -r api/requirements.txt || true
    fi
    if [ -f frontend/package.json ] && command -v npm >/dev/null 2>&1; then
      cd frontend && npm install
    fi
  before_remove: ""

agent:
  max_concurrent_agents: 5
  max_turns: 20

codex:
  command: codex --config shell_environment_policy.inherit=all --config 'model="gpt-5.5"' --config model_reasoning_effort=high app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite

sandbox:
  planning_writable_paths:
    - .symphony/initiatives/{{ initiative.slug }}/
  execution_writable_paths:
    - "{{ workspace.path }}/"
  fail_on_planning_diff_outside_initiative: true
  fail_on_execution_diff_outside_workspace: true
---

You are working on a Linear ticket `{{ issue.identifier }}` for the SOG project.

{% if attempt %}
Continuation context:

- This is retry attempt #{{ attempt }} because the ticket is still in an active state.
- Resume from the current workspace state instead of restarting from scratch.
- Do not repeat already-completed investigation or validation unless needed for new code changes.
{% endif %}

Issue context:
Identifier: {{ issue.identifier }}
Title: {{ issue.title }}
Current status: {{ issue.state }}
Labels: {{ issue.labels }}
URL: {{ issue.url }}

Description:
{% if issue.description %}
{{ issue.description }}
{% else %}
No description provided.
{% endif %}

Operating rules:

1. Read `AGENTS.md` first.
2. Treat `.kimi/` only as historical documentation when it is useful context; do not follow it as an orchestration chain.
3. Use Linear as the source of truth for work selection and status.
4. Use GitHub for code changes, branches, commits, pull requests, and review follow-up.
5. Keep exactly one persistent `## Codex Workpad` comment on the issue and update it in place throughout the run.
6. Treat ticket-provided `Validation`, `Test Plan`, and `Testing` sections as required acceptance input.
7. For browser or UI work, prefer Playwright CLI when validation needs a real browser.
8. Do not ask a human to perform follow-up steps unless blocked by missing required auth, permissions, or unavailable external systems.
9. Work only inside the provided repository workspace.

## Plan

- [ ] Reconcile the current ticket state, repo state, and the existing workpad comment.
- [ ] Sync the workspace, implement the requested change, and update the workpad as reality changes.
- [ ] Run targeted validation for the touched behavior.
- [ ] Update or open the GitHub PR and link the evidence back to the Linear issue.

## Acceptance Criteria

- [ ] The Linear issue is handled end-to-end in the current run.
- [ ] Code changes and PR state match the issue scope.
- [ ] Validation evidence is recorded in the workpad.
- [ ] Browser or UI work includes real validation proof when applicable.
