# PRD: Finalizar projeto SOG para homologacao operacional

Date: 2026-05-30

## Status

Planning artifact for Symphony phase `prd`.

This PRD is derived from:

- `.symphony/initiatives/finalizar-projeto/initiative.md`
- `.symphony/initiatives/finalizar-projeto/diagnosis.md`
- `.symphony/initiatives/finalizar-projeto/initiative.yml`

## Summary

Finalizar o SOG para uma homologacao operacional controlada em ambiente local Docker, usando SQLite, PJE/SISTJWEB reais com autenticacao interativa do usuario, automacao headless apos login, dashboard operacional em React + Vite + shadcn/UI, notificacoes por dashboard e Telegram, e validacao assistida com lote minimo de 10 processos reais.

O foco do produto e provar que o fluxo consegue operar um ciclo fechado de processos com rastreabilidade, idempotencia, revisao humana por processo e estados finais acionaveis. Esta homologacao nao e deploy de producao, nao inclui PostgreSQL, nao inclui backup sidecar e nao reativa a pasta `.kimi/` como orquestrador.

## Problem

O repositorio ja contem backend FastAPI, agente Python/Playwright, frontend React + Vite, SQLite compartilhado, rotas de controle do agente e testes parciais. Contudo, o desenho atual ainda e fila/processo-centrico e nao consegue provar o criterio principal de homologacao: um ciclo fechado iniciado pelo usuario, com snapshot de membros, UUID preservado, pausa/retomada, idempotencia e conclusao apenas quando todos os processos tiverem resultado acionavel.

Sem esse modelo, a operacao fica vulneravel a duplicidade, reprocessamentos implicitos, anexos repetidos no PJE, falta de historico confiavel e impossibilidade de explicar o que exatamente foi homologado.

## Goals

- Tornar o SOG verificavel para homologacao operacional local Docker.
- Introduzir o conceito de ciclo/lote do agente como entidade persistida e auditavel.
- Garantir que `Iniciar Agente` forme um lote fechado com processos novos capturados no PJE configurado e processos conhecidos explicitamente rearmados.
- Garantir que pausa, relogin e retomada preservem o mesmo ciclo, UUID e snapshot.
- Garantir que nova execucao sobre processos ja tratados nao duplique registros, guias, logs criticos ou anexos no PJE.
- Permitir revisao e aprovacao humana processo por processo antes de emitir demonstrativo e anexar no PJE real.
- Expor um dashboard autenticado, compacto e operacional, com tabs `Ciclo atual`, `Processos` e `Historico`.
- Enviar notificacoes Telegram agregadas e sem dados sensiveis para eventos definidos.
- Validar com testes alvo e execucao assistida local Docker com pelo menos 10 processos reais.

## Non-Goals

- Deploy em VPS, producao ou homologacao remota.
- Migracao para PostgreSQL.
- Backup sidecar.
- SMTP/e-mail como requisito desta homologacao.
- Comandos remotos via Telegram.
- Aprovacao em lote.
- Descarte/encerramento manual definitivo de ciclo pausado.
- Arquitetura enterprise grade alem do necessario para homologacao local controlada.
- Uso de `.kimi/` como fluxo ativo de CEO/QA/Reviewer/orquestracao.
- Automacao E2E completa e nao assistida contra PJE/SISTJWEB reais.

## Users and Actors

- Operadora/contadora do TJDFT: acompanha ciclo, revisa guias, aprova ou rejeita processos e consulta historico.
- Administrador tecnico do SOG: configura `.env`, Docker local, credenciais tecnicas e acompanha logs.
- Agente automatizado: captura processos, consulta dados, preenche SISTJWEB, gera evidencias e prepara guias para revisao.
- API/dashboard: controla agente, exibe ciclo, processos, detalhes, historico, autenticacao e acoes humanas.
- PJE/SISTJWEB/Datajud: sistemas externos reais usados durante homologacao assistida.
- Linear/GitHub via Symphony: rastreabilidade posterior de issues, PRs e validacoes.

## Definition of Ready for Homologation

O SOG esta pronto para homologacao operacional controlada quando:

- A aplicacao sobe em Docker local com API, frontend, agente e nginx.
- A configuracao minima obrigatoria esta documentada e validada sem exigir SMTP.
- O usuario consegue iniciar um ciclo pelo dashboard autenticado.
- O ciclo recebe UUID persistido, rotulo por data/hora de inicio e snapshot persistido de membros.
- O login PJE/SISTJWEB ocorre em browser visivel com credenciais inseridas manualmente pelo usuario.
- Apos autenticacao, a automacao continua headless ate todos os processos do ciclo terem resultado acionavel.
- O dashboard mostra ciclo atual/ultimo ciclo, progresso, contagens, membros, acoes e excecoes.
- Reprocessamento so ocorre apos acao explicita `Reprocessar` em processo elegivel.
- Pausa/relogin/retomada preservam UUID e snapshot.
- Aprovacao humana individual dispara emissao do demonstrativo e anexo no PJE real.
- Sucesso final vira `emitido`; falhas de emissao/anexo viram `erro` com `erro_msg` e logs claros.
- Telegram notifica apenas os eventos exigidos com conteudo agregado e sem dados sensiveis.
- Testes alvo passam e a execucao assistida com 10 processos registra tempos, gargalos e resultados finais.

## Functional Requirements

### 1. Local Docker and Configuration

- The homologation runtime must be local Docker only.
- The required local configuration must include:
  - `DASHBOARD_SENHA_HASH`
  - `JWT_SECRET_KEY`
  - `DATAJUD_API_KEY`
  - `PJE_URL`
  - `PJE_ETIQUETA`
  - `SISTJ_URL`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- `.env.example` and runtime validation must reflect Telegram as required for this homologation.
- SMTP configuration must not block startup or homologation.
- Secrets must not be persisted in versioned files, database records, logs or PRD/issues.

### 2. Agent Cycle Model

- Add first-class cycle persistence in SQLite/shared DB.
- Each cycle must have:
  - UUID
  - start timestamp
  - display label based on start date/time
  - status
  - membership snapshot
  - aggregate counters
  - total cycle time
  - per-process timing
  - bottleneck notes or structured observations when available
  - pause/resume timestamps when applicable
- UUID must be copyable in the cycle detail but hidden from the main table.
- Cycle history must use the persisted membership snapshot, not inference from current process status.

### 3. Closed Batch Membership

- Clicking `Iniciar Agente` must form a closed batch from:
  - new processes captured from configured PJE folder/label at trigger time
  - known processes explicitly selected/rearmed by the user
- Processes discovered after the cycle starts must not change the active cycle.
- The cycle is complete only when every member reaches an actionable outcome:
  - `aguardando_aprovacao`
  - `pendente_manual`
  - `erro`
- Processes in final/actionable states must not be reprocessed automatically.

### 4. Agent Control, Pause and Resume

- `Iniciar Agente` must be disabled while a cycle is running.
- If a paused cycle exists, `Iniciar Agente` must resume that cycle by default instead of creating a new cycle.
- The primary control must change state:
  - stopped/no paused cycle: `Iniciar Agente`
  - running: `Parar Agente`
  - paused/interrupted: resume/status-appropriate control
- `Parar Agente` must be cooperative: stop after the current safe step, preserve snapshot and UUID, and mark the cycle paused/interrupted.
- Manual permanent termination/discard of paused cycles is out of scope.
- Concurrent cycles against PJE/SISTJWEB, storage state and SQLite must be prevented in UI, API and agent state.

### 5. Authentication and Session Expiration

- After `Iniciar Agente`, the user must authenticate manually in a headed browser, including password and 2FA when required.
- After successful authentication, storage state may be saved and the agent continues headless.
- If PJE/SISTJWEB session expires, the cycle must pause and request user relogin.
- Relogin must continue the same cycle and must not duplicate completed work.
- The dashboard must show a fixed relogin banner at the top of `Ciclo atual`.
- When technically possible, the banner must expose an action to open login or continue authentication.

### 6. Process Outcomes and Human Approval

- Automation boundary: the agent prepares all selected processes until each process has a guide ready for review or an exception state.
- `aguardando_aprovacao` means the guide is ready for human analysis and approval.
- Human review and approval are per process.
- When approved, the system must emit the demonstrativo and attach it to the corresponding real PJE process.
- Successful emission and attachment must set final status `emitido`.
- Emission or attachment failure must set status `erro`, with clear `erro_msg` and logs.
- Individual process failures must not block the entire cycle.

### 7. Reprocess/Rearm and Audit

- Add a `Reprocessar` action in process detail for statuses:
  - `erro`
  - `pendente_manual`
  - `rejeitado`
- Reprocessing must be explicit and user-triggered.
- The action must:
  - write an audit/log entry
  - mark the process for inclusion in the next started cycle
  - avoid immediate background processing outside a new cycle start
- The rearm flag/state must be consumed by the next cycle and not reused indefinitely.

### 8. Idempotency

- Re-running with already processed processes must not duplicate:
  - process records
  - guides/demonstrativos
  - critical logs
  - PJE attachments
- Only explicitly rearmed processes can be processed again.
- Idempotency must be covered by targeted automated tests and by the assisted 10-process homologation run.

### 9. Telegram Notifications

- Implement Telegram as notify-only.
- Required configuration:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- Required events:
  - session expired / relogin required
  - batch completed summary
  - fatal error with agent paused
- Telegram batch summary must include only:
  - total
  - `aguardando_aprovacao` count
  - `pendente_manual` count
  - `erro` count
  - `emitido` count
  - total cycle time
  - dashboard hint
- Telegram payloads must not include:
  - process numbers
  - party names
  - document details
- Telegram sending must be testable with mocked HTTP.

### 10. Cycle API and Schemas

- API must expose enough data for:
  - current or last cycle
  - cycle detail with UUID
  - cycle process membership snapshot
  - cycle progress and status counts
  - cycle history
  - pause/resume/control state
  - rearm/reprocess action
  - relogin-required state
- Existing routes may be preserved when useful, but response schemas must align with the cycle-first dashboard.

### 11. Dashboard UX

- Keep React + Vite.
- Use shadcn/UI compatible with Vite.
- Replace current UI primitives with shadcn/UI components without migrating to Next.js.
- Preserve existing pages, routes and flows where they remain useful.
- Post-login home must be `Ciclo atual`, not a simple queue.
- Main navigation must use tabs:
  - `Ciclo atual`
  - `Processos`
  - `Historico`
- Visual direction:
  - institutional discreet
  - compact
  - high contrast status legibility
  - no required charts
- The UI must be practical for an average daily volume of around 50 processes.

### 12. Dashboard Cycle Tab

- `Ciclo atual` must show:
  - agent status
  - `Iniciar Agente` / `Parar Agente` stateful control
  - current or last cycle summary
  - batch progress
  - status counts
  - relogin alert banner when needed
  - compact process review list
- Cycle process table minimum columns:
  - `Processo`
  - `Status`
  - `Etapa atual`
  - `Guia`
  - `Tempo`
  - `Acao`
- Row actions:
  - `aguardando_aprovacao`: `Revisar`
  - `emitido`: `Ver comprovante/detalhe`
  - `erro`: `Ver erro` or `Reprocessar`
  - `pendente_manual`: `Ver erro` or `Reprocessar`
  - `rejeitado`: `Reprocessar`
  - running/in-progress: status only, no primary action

### 13. Dashboard Process and History Tabs

- `Processos` must list all processes in the database.
- `Processos` must include quick filters and default focus on actionable items.
- `Historico` must include:
  - process history
  - agent cycle history
- `Historico` may use a simple segmented filter to separate histories.

### 14. Theme

- Add light/dark theme support.
- Initial mode must follow `prefers-color-scheme`.
- User-selected mode must persist in `localStorage`.
- Toggle must be icon-only with Sun/Moon icon and tooltip in the global header.

## Data Requirements

- SQLite remains the only database for this homologation.
- New schema must be mirrored between agent/shared schema definitions where applicable.
- Cycle and membership data must be queryable for dashboard and tests.
- Logs and audit records must support investigation without storing secrets.
- Telegram summaries must be generated from aggregate cycle data, not raw sensitive details.

## Validation Requirements

### Automated Tests

Add targeted tests for:

- cycle creation and UUID persistence
- closed-batch membership snapshot
- cycle status transitions
- pause/resume preserving cycle UUID
- relogin-required pause state
- rearm/reprocess audit trail
- rearm consumption by next cycle
- idempotent rerun behavior
- Telegram event payload privacy
- cycle API current/detail/history responses
- dashboard tabs and post-login cycle home
- theme toggle persistence
- cycle table row actions
- relogin banner behavior

### Local Docker Smoke

Validate local Docker startup for:

- API
- frontend
- agente
- nginx
- SQLite volume/data path
- required env validation

Suggested command family, adjusted to the repo scripts available when implemented:

```bash
docker-compose up --build -d
docker logs custas-agente
docker exec custas-agente python /app/src/main.py
```

### Browser/UI Proof

For UI implementation issues, record Playwright evidence that:

- login lands on `Ciclo atual`
- tabs render and navigate correctly
- cycle table is readable
- status badges are legible in light and dark mode
- relogin banner appears when API state requires it
- row actions match process status

### Assisted Real Homologation

Run an assisted local Docker validation with at least 10 real processes:

- User starts agent from dashboard.
- User completes PJE/SISTJWEB login manually.
- Agent continues headless.
- Cycle membership snapshot remains fixed.
- Every process reaches `aguardando_aprovacao`, `pendente_manual` or `erro`.
- At least one approval path validates demonstrativo emission and PJE attachment when operationally allowed.
- A repeat run over already handled processes does not duplicate records, guides, critical logs or PJE attachments.
- Record total cycle time, per-process time, bottlenecks and final outcomes.

## Acceptance Criteria

- PRs implementing this initiative do not modify `.kimi/` as an active orchestration path.
- The system can be configured and started in local Docker with documented required env vars.
- The API and DB expose a first-class agent cycle with UUID, label, status, membership snapshot and history.
- `Iniciar Agente` creates or resumes the correct cycle according to paused/running state.
- Cycle membership is closed at start and persisted.
- Process failures remain visible and actionable without blocking the rest of the cycle.
- Reprocessing is explicit, audited and consumed by the next cycle only.
- Idempotency tests prove no duplicate internal artifacts for already processed processes.
- Telegram sends only the three required notify-only event types and excludes sensitive process details.
- Dashboard home is the cycle panel with tabs `Ciclo atual`, `Processos` and `Historico`.
- UI uses React + Vite + shadcn/UI and includes light/dark theme persistence.
- Automated test suite covers the core cycle, API, notification and UI behavior.
- Assisted 10-process local Docker run is documented with evidence and residual risks.

## Risks and Mitigations

- Real PJE/SISTJWEB login may be brittle.
  - Mitigation: keep external validation assisted and avoid requiring full unattended E2E.
- Cycle model touches shared DB, agent, API and UI.
  - Mitigation: implement in slices with focused tests before UI expansion.
- Idempotency around PJE attachments is high risk.
  - Mitigation: require explicit checks before attach and record evidence in homologation.
- shadcn/UI replacement is broad.
  - Mitigation: keep the dashboard compact, preserve useful flows and avoid visual rewrites beyond required components.
- SQLite concurrency can be fragile if cycles overlap.
  - Mitigation: prevent concurrent cycles at UI, API and agent state levels.

## Implementation Slices for Issues

The downstream `issues` phase should prefer small, verifiable slices:

1. Add SQLite/shared DB cycle persistence and membership snapshot.
2. Implement closed-batch start/resume semantics in agent service.
3. Implement pause/relogin/resume state transitions preserving UUID.
4. Implement reprocess/rearm action with audit and next-cycle consumption.
5. Add idempotency guards and tests for already processed processes.
6. Add Telegram notify-only sender, config validation and privacy tests.
7. Add cycle API schemas/endpoints for current/detail/history/control state.
8. Rebuild dashboard shell with shadcn/UI tabs, theme toggle and cycle home.
9. Implement cycle table, row actions, relogin banner and process/history tabs.
10. Add Docker smoke checks and assisted 10-process homologation checklist/evidence template.

## Open Questions

No open product questions block issue decomposition. External validation still depends on real PJE/SISTJWEB credentials and user permission during execution, but that is an operational constraint rather than a PRD ambiguity.
