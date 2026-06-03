# Navegador de sessão abre SISTJWEB de forma persistente

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 10, 11, 15, 27, 28

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Build the SISTJWEB half of the Navegador de sessão do SOG. The operador must be able to open SISTJWEB independently from PJe in a visible, persistent browser profile controlled by SOG, complete login and 2FA, and leave that session available for validation and later agent use.

This slice must keep PJe and SISTJWEB login actions independent.

## Acceptance criteria

- [ ] The operador can trigger an independent "Abrir SISTJWEB" action from the SOG operator flow.
- [ ] SISTJWEB opens in a visible Navegador de sessão do SOG with a persistent profile.
- [ ] The browser remains open long enough for manual SSO/2FA without automation timeout closing it.
- [ ] SOG does not store SISTJWEB username or password.
- [ ] Reopening SISTJWEB reuses the SOG session profile instead of creating unrelated ephemeral Chromium instances.
- [ ] Automated tests or a documented smoke prove the SISTJWEB opening flow does not depend on PJe.

## Blocked by

None - can start immediately
