# Banco compartilhado por Fronteira de domínio

Status: ready-for-agent
Type: AFK
Labels: ready-for-agent
User stories covered: 36, 37

## Parent

Source PRD: `docs/PRD2.md`

## What to build

Organize the Banco compartilhado implementation by Fronteira de domínio without adding speculative repository classes. The target seams are Processos e aprovação, Agente e ciclos, Tarefas e sessões externas, and Infraestrutura de banco.

## Acceptance criteria

- [ ] Dead or obsolete database functions are removed before splitting implementation.
- [ ] Processos e aprovação behavior is localized behind its domain-facing module.
- [ ] Agente e ciclos behavior is localized behind its domain-facing module.
- [ ] Tarefas e sessões externas behavior is localized behind its domain-facing module.
- [ ] Infraestrutura de banco does not carry process, agent or task language.
- [ ] No repository/service/factory layer is introduced for the single SQLite source.
- [ ] Tests target behavior through the domain-facing seams rather than SQL internals.

## Blocked by

- `10-contrato-compartilhado-canonico.md`
