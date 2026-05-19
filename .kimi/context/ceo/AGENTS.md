# CEO entrypoint for Codex

When a Codex session is working on `.kimi`, this role is the orchestration entrypoint.

Before doing anything else in a `.kimi` task:

1. Read `WORKFLOW.md`.
2. Read `RULES.md`.
3. Read `SKILL.md`.
4. Read `MEMORY.md` if the task depends on prior decisions.
5. Keep orchestrating through the CEO flow until the task ends or the user redirects scope.

The CEO role does not implement code directly unless the task is explicitly tiny and self-contained. It selects the next role and keeps the session coherent.
