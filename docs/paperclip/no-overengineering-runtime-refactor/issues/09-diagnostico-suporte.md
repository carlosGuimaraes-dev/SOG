# Diagnóstico para suporte com contato

Status: ready-for-agent
Type: HITL
Labels: ready-for-agent
User stories covered: 6, 24, 25

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Add Diagnóstico para suporte for runtime preparation and local startup failures. The operador should see a simple message with support telephone/email, while technical details remain available for support to understand the failing runtime step.

This issue is HITL because the final support phone/email values must be supplied or confirmed.

## Acceptance criteria

- [ ] Runtime preparation failures show a simple operator-facing message.
- [ ] The message includes support telephone and email.
- [ ] Diagnostic detail identifies the failing step, such as Node.js, npm, Docker CLI, WSL or container startup.
- [ ] Technical detail is available for support without requiring the operator to interpret stack traces.
- [ ] Diagnostics are reachable from the dashboard configuration tab or startup failure flow.
- [ ] Tests cover operator-facing and support-facing diagnostic output.

## Blocked by

- `08-preparo-runtime-interno.md`
