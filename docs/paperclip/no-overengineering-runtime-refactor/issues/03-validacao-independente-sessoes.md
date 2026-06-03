# Validação independente das sessões externas

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 12, 13, 16, 17, 26

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Add independent validation for PJe and SISTJWEB sessions after the operador logs in through the Navegador de sessão do SOG. The Dashboard local must show whether each external session is pending, active, expired, or unavailable without one system blocking the other.

## Acceptance criteria

- [ ] PJe session validation can run and report status without requiring SISTJWEB to be active.
- [ ] SISTJWEB session validation can run and report status without requiring PJe to be active.
- [ ] The dashboard shows separate session states for PJe and SISTJWEB.
- [ ] Pending login and expired session messages are actionable for the operador.
- [ ] Validation does not ask for dashboard login or JWT.
- [ ] Tests prove PJe and SISTJWEB validation states are independent.

## Blocked by

- `01-navegador-sessao-pje.md`
- `02-navegador-sessao-sistjweb.md`
