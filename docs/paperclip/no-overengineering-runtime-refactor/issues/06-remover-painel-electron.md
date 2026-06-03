# Remover painel operacional do Electron

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 7, 30, 31

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Reduce Electron to Casca local. Electron should prepare/start/open the local SOG experience but should not own a permanent operational panel or configuration UI. Operator configuration must live in the Dashboard local.

## Acceptance criteria

- [ ] Configuration that belongs to SOG operation is available through the dashboard configuration tab.
- [ ] Electron no longer presents a parallel operational/configuration surface for the same workflow.
- [ ] Electron still starts or opens the local SOG experience.
- [ ] Existing desktop verification is updated to reflect Electron as Casca local.
- [ ] Tests or desktop contract checks prove removing the Electron panel does not remove the operator configuration path.

## Blocked by

- `05-aba-config-dashboard.md`
