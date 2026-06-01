> Status deste arquivo: artefato histórico de orquestração.
> Ele registra contexto legado de execução e não substitui a documentação
> canônica do produto e do runtime atual.
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
    - Rework
    - Merging
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
  phases:
    - elicit
    - diagnose
    - prd
    - issues
    - review
    - approve
    - handoff
    - export
  interactive_phases:
    - elicit
    - approve
  approval_required: true

artifacts:
  required:
    - initiative.yml
    - initiative.md
    - diagnosis.md
    - prd.md
    - issues.draft.md
    - review.md
    - issues.approved.md
    - handoff.md
    - export.json

workspace:
  root: ~/code/symphony-workspaces
  issue_path: "{{ issue.identifier }}"

hooks:
  after_create: |
    git clone --depth 1 "https://github.com/carlosGuimaraes-dev/SOG.git" .
    if [ -f .env.example ] && [ ! -f .env ]; then
      cp .env.example .env
    fi
    if command -v mise >/dev/null 2>&1; then
      mise trust
      mise install
    fi
  before_remove: ""

agent:
  max_concurrent_agents: 10
  max_turns: 20

codex:
  command: codex --config shell_environment_policy.inherit=all --config 'model="gpt-5.5"' --config model_reasoning_effort=high app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite

sandbox:
  planning_writable_roots:
    - .symphony/initiatives/{{slug}}/
  execution_writable_roots:
    - "{{workspace}}"
  fail_on_planning_diff_outside_initiative: true
  fail_on_execution_diff_outside_workspace: true

execution:
  legacy_workflow_compatible: true
  review_state: Human Review
  completion_requires_pr: true
---

You are working on a Linear ticket `{{ issue.identifier }}`.

{% if attempt %}
Continuation context:

- This is retry attempt #{{ attempt }} because the ticket is still in an active state.
- Resume from the current workspace state instead of restarting from scratch.
- Do not repeat already-completed investigation or validation unless needed for new code changes.
- Do not end the turn while the issue remains in an active state unless you are blocked by missing required permissions, secrets, or external access.
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

1. This is an unattended orchestration session. Do not ask a human to perform follow-up steps unless blocked by missing required auth, permissions, or unavailable external systems.
2. Use Linear as the source of truth for work selection and status.
3. Use GitHub for code changes, branches, commits, PRs, and review follow-up.
4. Keep exactly one persistent `## Codex Workpad` comment on the issue and update it in place throughout the run.
5. Treat ticket-provided `Validation`, `Test Plan`, and `Testing` sections as required acceptance input.
6. For browser or UI work, prefer Playwright CLI and capture proof when the task benefits from it.
7. Work only inside the provided repository workspace.
8. Use `.codex/skills/push/SKILL.md` to publish code and create or update the PR.
9. Use `.codex/skills/land/SKILL.md` to monitor checks, resolve merge/CI failures,
   and squash-merge the PR. Do not call `gh pr merge` directly.
10. Do not mark the issue `Done` until the PR is merged, unless the issue
    explicitly allows direct completion without PR review.

## Plan

- [ ] Reconcile the current ticket state, repo state, and existing workpad comment.
- [ ] Sync the workspace, implement the requested change, and update the workpad as reality changes.
- [ ] Run targeted validation for the touched behavior.
- [ ] Update or open the GitHub PR and link the evidence back to the Linear issue.
- [ ] Move the issue to `Merging`, run the `land` skill, and merge the PR when green.
- [ ] Move the issue to `Done` only after merge or approved direct completion.

## Acceptance Criteria

- [ ] The Linear issue is handled end-to-end in the current run.
- [ ] Code changes and PR state match the issue scope.
- [ ] Validation evidence is recorded in the workpad.
- [ ] The PR is merged through the `land` skill, or the workpad records why the issue required human review or direct completion.
- [ ] Browser or UI work includes Playwright proof when applicable.
