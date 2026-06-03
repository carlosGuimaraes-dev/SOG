# Contrato compartilhado canônico

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 32, 33, 34, 35

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Make `shared/sog_shared` the canonical Contrato compartilhado and Banco compartilhado source. Remove domain schema/model drift across API, agente, frontend and tests. API may keep Contratos de apresentação da API, and frontend may keep Modelos de tela, but they must not redefine shared domain language.

## Acceptance criteria

- [ ] There is one canonical SQL schema source for the Banco compartilhado.
- [ ] API and agente tests use the shared schema source.
- [ ] API models do not duplicate shared domain models unless they are presentation contracts.
- [ ] Frontend types that duplicate domain/API contracts are removed or converted into presentation-only Modelos de tela.
- [ ] Contract tests prove the shared schema/models are importable and consistent for runtime callers.
- [ ] No dashboard-auth-only schema/model concepts remain as part of the shared domain.

## Blocked by

None - can start immediately
