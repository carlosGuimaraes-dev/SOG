# Preparo automatizado do runtime interno

Status: ready-for-agent
Type: HITL
Labels: ready-for-agent
User stories covered: 1, 2, 3, 4, 5, 22, 23, 25

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Implement the executable/runtime preparation flow that checks Node.js, npm, Docker CLI and WSL, asks for Autorização de instalação local when something is missing, explains elevation before UAC, and preserves enough state for Retomada após reinicialização.

This issue is HITL because sources of installers, exact elevation policy, and reboot behavior should be confirmed before AFK implementation.

## Acceptance criteria

- [ ] Runtime check reports Node.js present/missing.
- [ ] Runtime check reports npm present/missing.
- [ ] Runtime check reports Docker CLI present/missing without using Docker Desktop as the user journey.
- [ ] Runtime check reports WSL present/enabled or missing/disabled.
- [ ] Missing dependencies trigger an operator authorization prompt before installation/configuration continues.
- [ ] UAC/elevation is explained before the elevated action is requested.
- [ ] Reboot-required state is persisted and can be resumed.
- [ ] Tests or documented simulations cover each missing-dependency outcome.

## Blocked by

None - can start immediately
