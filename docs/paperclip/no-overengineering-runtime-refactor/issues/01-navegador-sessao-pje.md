# Navegador de sessão abre PJe de forma persistente

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 9, 11, 15, 27, 28

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Build the PJe half of the Navegador de sessão do SOG. The operador must be able to open PJe from the SOG flow in a visible, persistent browser profile controlled by SOG, complete login and 2FA without the browser closing, and leave that session available for validation and later agent use.

This slice must not introduce dashboard login, store external credentials, or copy the session into a separate browser as the primary path.

## Acceptance criteria

- [ ] The operador can trigger an independent "Abrir PJe" action from the SOG operator flow.
- [ ] PJe opens in a visible Navegador de sessão do SOG with a persistent profile.
- [ ] The browser remains open long enough for manual SSO/2FA without automation timeout closing it.
- [ ] SOG does not store PJe username or password.
- [ ] Reopening PJe reuses the SOG session profile instead of creating unrelated ephemeral Chromium instances.
- [ ] Automated tests or a documented smoke prove the PJe opening flow does not depend on SISTJWEB.

## Blocked by

None - can start immediately
