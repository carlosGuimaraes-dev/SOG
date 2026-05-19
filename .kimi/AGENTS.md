# Codex bridge for `.kimi`

This folder is the source of truth for the Kimi-style agent system in this repo.
When working inside `.kimi`, follow these rules:

1. Treat the **CEO role** as the entrypoint for any new Codex session that works on `.kimi`.
2. Start by reading `.kimi/context/ceo/WORKFLOW.md` and `.kimi/context/ceo/RULES.md`.
3. Use the CEO workflow to decide which subordinate role or plan to follow next.
4. Keep the CEO role active for the full task until the session's `.kimi` work is finished.
5. Then continue with the nearest `AGENTS.md` file in each subtree before editing anything there.
6. Read the role docs in this order when applicable:
   - `SOUL.md`
   - `RULES.md`
   - `SKILL.md`
   - `TOOLS.md`
   - `WORKFLOW.md`
   - `MEMORY.md`
7. Keep changes surgical. Do not refactor the Kimi system unless the user asks for it.

Directory map:

- `agents/` - declarative agent definitions.
- `context/` - role instructions and memory for each persona.
- `prompts/` - system prompts used by the Kimi agent configs.
- `skills/` - reusable task-specific guidance.
- `plans/` - technical plans produced for implementation work.

Codex usage note:

- If a task references a Kimi role, mirror that role by reading the matching files in `context/<role>/`.
- If a task references a Kimi plan, use the matching file in `plans/` as the implementation scope.
- Do not assume Kimi-specific tool names exist in Codex; translate them to the tools available in the current environment.
