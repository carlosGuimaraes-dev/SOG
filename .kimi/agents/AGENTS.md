# Agent definitions for Codex

These YAML files are declarative agent configs from the Kimi system.

Guidance:

- Treat `name` as the role identifier.
- Treat `system_prompt_path` as a pointer to the role prompt in `prompts/`.
- Treat `tools` as the capability set the role expects, not as Codex commands.
- Do not edit these files unless the agent definition itself must change.

Before changing an agent config, read the matching prompt and the role docs under `context/<role>/`.
