# Dashboard local sem autenticação própria

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 18, 19, 21, 38, 39

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Remove dashboard-local authentication concepts from the runtime. The Dashboard local must open directly, with no `/login` redirect, JWT, refresh token, dashboard user identity, or multiuser audit. Preserve rastreabilidade operacional and aprovação humana.

## Acceptance criteria

- [ ] The local dashboard opens without requiring login.
- [ ] Dashboard routes do not require JWT or refresh tokens in the local scope.
- [ ] Login screen and auth-provider behavior are removed from the operator path.
- [ ] Refresh-token schema/model concepts tied only to dashboard login are removed or made irrelevant to runtime.
- [ ] Approval and rejection actions still require explicit operator action.
- [ ] Tests prove the dashboard does not redirect to `/login`.

## Blocked by

None - can start immediately
