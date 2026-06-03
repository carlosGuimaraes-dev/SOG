# Estado operacional sem fila técnica

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 18, 20, 21

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Ensure the Dashboard local presents Estado operacional instead of a technical queue administration surface. The operador should see progress, blockers, reauthentication needs and resumable state, not manipulate internal jobs directly.

## Acceptance criteria

- [ ] The dashboard summarizes operational progress and blockers in operator language.
- [ ] Reauthentication needs for PJe/SISTJWEB are shown as guided actions, not raw job states.
- [ ] Internal task details are not exposed as a queue the operador must administer.
- [ ] Rastreabilidade operacional remains available for support and troubleshooting.
- [ ] Tests cover the displayed operator state for pending login, active sessions, blocked work and resumable work.

## Blocked by

- `03-validacao-independente-sessoes.md`
- `05-aba-config-dashboard.md`
