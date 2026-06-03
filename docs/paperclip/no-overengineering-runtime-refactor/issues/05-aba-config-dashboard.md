# Aba de configuração no Dashboard local

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 7, 8, 9, 10, 16, 17, 20, 31

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Add an Aba de configuração inside the Dashboard local as the operator-facing place for SOG configuration, session actions, and operational status. This tab becomes the home for opening PJe, opening SISTJWEB, validating sessions, showing runtime state, and guiding reauthentication.

## Acceptance criteria

- [ ] The dashboard has a configuration tab reachable from the main navigation.
- [ ] The tab exposes separate actions for opening PJe and SISTJWEB.
- [ ] The tab has space for independent PJe/SISTJWEB session status.
- [ ] The tab can show runtime/support diagnostics as they become available.
- [ ] The tab is usable without any dashboard login.
- [ ] Frontend tests cover the tab as the operator-facing configuration surface.

## Blocked by

None - can start immediately
