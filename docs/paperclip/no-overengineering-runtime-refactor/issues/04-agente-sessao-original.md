# Agente opera na sessão original do operador

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 14, 20, 27, 28, 29, 41

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Make the agente operate through the same persistent Navegador de sessão do SOG where the operador completed PJe/SISTJWEB login and 2FA. Replace the copied-session choreography as the main path: the agent should not depend on exporting `storage_state` from one browser and importing it into another browser to work.

## Acceptance criteria

- [ ] The agent uses the original SOG-controlled browser/session profile for external operations.
- [ ] The main successful path no longer requires copying `storage_state` into a separate browser.
- [ ] Expired external sessions move the system into a reauthentication flow through the dashboard.
- [ ] Reauthentication preserves the cycle enough for the operator to resume after login.
- [ ] Tests cover the session module interface rather than low-level storage file choreography.
- [ ] The old copied-session path is removed or left only as a clearly non-primary compatibility fallback if absolutely necessary.

## Blocked by

- `03-validacao-independente-sessoes.md`
