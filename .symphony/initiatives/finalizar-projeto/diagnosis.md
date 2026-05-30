# Diagnosis

Date: 2026-05-30

## Scope

This diagnosis inspects the current SOG repository against the confirmed initiative goal: controlled local Docker homologation with real PJE/SISTJWEB, interactive user login/2FA, headless automation after authentication, a closed batch of 10 processes, SQLite only, Telegram notification, and a simple React + Vite dashboard using shadcn/UI.

The legacy `.kimi/` material was treated as historical context only.

## Feedback Loop

The Symphony planning runner was first exercised from `/Users/carlosguimaraes/Projects/SOG` and failed because `project-root` was outside the configured workspace root. A detached worktree was created at `/Users/carlosguimaraes/code/symphony-workspaces/SOG-finalizar-projeto`, which satisfies the Symphony workspace guard.

The automated `initiative run ... diagnose` command started but exited without writing `diagnosis.md` or changing phase state. No useful Symphony/Codex log was found. This diagnosis was therefore produced directly from repository inspection using the `initiative-diagnose` skill.

## Architecture

The system is a Dockerized full-stack app:

- `agente/`: Python automation service using Playwright for PJE/SISTJWEB.
- `api/`: FastAPI dashboard backend.
- `frontend/`: React + Vite dashboard.
- `shared/`: shared Python package for SQLite access, config, and schemas.
- `nginx/`: reverse proxy.
- `dados/`: SQLite database, screenshots, and generated demonstrativos.

Local development uses `docker-compose.dev.yml` with API, frontend, agente, and nginx. Production compose is more hardened, but the initiative explicitly targets local Docker only.

## Entry Points

- API app: `api/src/app.py`
- Agent control API: `api/src/rotas/agente.py`
- Long-running agent service: `agente/src/servico.py`
- Agent pipeline: `agente/src/pipeline.py`
- PJE client: `agente/src/modulos/pje.py`
- SISTJWEB client: `agente/src/modulos/sistjweb.py`
- Browser auth manager: `agente/src/modulos/auth_manager.py`
- SQLite schema: `agente/src/banco/schema.sql` and `shared/sog_shared/schema.sql`
- Shared DB functions: `shared/sog_shared/db.py`
- Frontend root/routes: `frontend/src/App.tsx`
- Current queue page: `frontend/src/pages/Fila.tsx`
- Current history page: `frontend/src/pages/Historico.tsx`

## Current Fit

The code already supports several required foundations:

- API endpoints exist for `POST /agente/iniciar`, `POST /agente/parar`, and `GET /agente/status`.
- `AgenteServico` has a simple state machine with `parado`, `autenticando`, `executando`, `aguardando_login`, `erro`, and `parando`.
- `AuthManager` already models the desired authentication shape: try headless with storage state, open a visible browser for manual login when needed, save storage state, then reopen headless.
- Existing statuses include `aguardando_aprovacao`, `pendente_manual`, `erro`, `rejeitado`, and `emitido`.
- There are targeted tests across API, agent parsing/rules/service, frontend queue/detail/history, and polling behavior.
- The frontend is already React + Vite and has custom UI primitives that can be replaced by shadcn/UI without migrating framework.

## Gaps Against Elicitation

### Agent Cycle Model

The confirmed domain now centers on an agent cycle/batch. The current schema has `agente_controle` and `agente_tarefas`, but no first-class cycle table with UUID, start timestamp label, membership snapshot, status, timing, or aggregate counters.

Required additions:

- Persist cycle UUID.
- Display cycle by start date/time.
- Preserve UUID across pause/resume.
- Persist membership snapshot at cycle start.
- Track cycle status, aggregate outcomes, total time, per-process timing, and bottlenecks.
- Keep cycle history.

### Closed Batch Semantics

The current agent loop processes pending tasks and runs `rodar_pipeline()` / `emitir_pendentes()` by iteration. The elicited behavior requires a closed set formed at `Iniciar Agente`: new PJE processes plus explicitly rearmed known processes. Processes discovered later must belong to a later cycle.

This requires making batch formation explicit before processing begins.

### Reprocessing and Audit

There is an API surface for actions and tasks, including reprocess-related behavior, but the elicitation requires a dashboard detail action `Reprocessar` for `erro`, `pendente_manual`, and `rejeitado`, with audit/log entry and a state/flag consumed by the next batch.

The diagnosis should treat this as a core implementation slice, not a UI-only change.

### Pause, Resume, and Stop

The current `parar` command stops the service loop. The elicited behavior is softer: `Parar Agente` should cooperatively stop after the current step, mark the cycle paused/interrupted, preserve the batch snapshot and UUID, and let `Iniciar Agente` resume the paused cycle by default.

This is not fully represented in current `agente_controle`.

### Session Expiration Notification

The agent can enter `aguardando_login` when reauthentication is needed. Current notification support is e-mail only (`agente/src/utils/notificador.py`) and configuration has SMTP only. Telegram is not implemented.

Required additions:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- Telegram notify-only sender
- Dashboard relogin banner
- Notifications for session expired, batch completed summary, and fatal paused error
- Telegram summaries must be aggregate-only, with no process numbers, party names, or document details.

### Dashboard UX

Current frontend routes are queue-first:

- `/` renders `Fila`
- `/historico` renders `Historico`
- `/detalhe/:id` renders process detail

The initiative requires a new dashboard shape:

- Post-login home is `Ciclo atual`.
- Separate tabs: `Ciclo atual`, `Processos`, `Historico`.
- Compact cycle summary plus process table, no charts required.
- Average daily operation should remain usable for about 50 processes.
- Table columns: `Processo`, `Status`, `Etapa atual`, `Guia`, `Tempo`, `Acao`.
- Contextual row actions by status.
- Authenticated dashboard may show process details; Telegram must not.
- Light/dark theme with Sun/Moon icon-only tooltip, initial `prefers-color-scheme`, local persistence.
- Replace all current UI primitives with shadcn/UI while keeping React + Vite and preserving useful routes/flows.

### Local Configuration

`.env.example` has dashboard, PJE, SISTJWEB, Datajud, SMTP, Playwright, and LLM variables. It does not yet include Telegram variables. SMTP is deferred and should not block homologation.

Required minimum for homologation:

- `DASHBOARD_SENHA_HASH`
- `JWT_SECRET_KEY`
- `DATAJUD_API_KEY`
- `PJE_URL`
- `PJE_ETIQUETA`
- `SISTJ_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Test Coverage Findings

Existing tests are useful but do not cover the new initiative-critical behavior:

- No tests for cycle UUID, cycle snapshot, cycle status transitions, or history.
- No tests for closed-batch membership.
- No tests proving idempotent re-run avoids duplicate records/guides/logs/PJE attachments.
- No tests for pause/resume preserving the same cycle UUID.
- No tests for Telegram notification payload privacy.
- No tests for shadcn/UI migration, tabs, or cycle panel.
- Existing frontend tests cover older queue/detail/history behavior.

The PRD should require targeted tests rather than full external E2E automation against PJE/SISTJWEB.

## Risks

- Real PJE/SISTJWEB login and 2FA will make full automation brittle; the correct acceptance path is assisted local Docker validation.
- Without a first-class cycle table, the main business criterion cannot be proven: all processes in a cycle reached an actionable outcome.
- Without idempotency checks, repeated `Iniciar Agente` can risk duplicate work or duplicate PJE attachments.
- Without a Telegram sender, session expiration may stall a headless run without timely user action.
- Replacing all UI primitives with shadcn/UI is broad; it should be done as a focused dashboard-system slice with tests and visual/browser validation.
- SQLite is acceptable for this homologation, but concurrent cycle execution must be prevented in UI/API/agent state.

## Affected Modules

Likely affected files and areas:

- `agente/src/banco/schema.sql`
- `shared/sog_shared/schema.sql`
- `shared/sog_shared/db.py`
- `agente/src/servico.py`
- `agente/src/pipeline.py`
- `agente/src/utils/notificador.py`
- `agente/src/config.py`
- `api/src/rotas/agente.py`
- `api/src/rotas/acoes.py`
- `api/src/schemas.py`
- new or existing API routes for cycle state/history
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/pages/Fila.tsx`
- `frontend/src/pages/Historico.tsx`
- `frontend/src/components/ui/*`
- new dashboard cycle components under `frontend/src/components/`
- tests under `api/tests`, `agente/tests`, and `frontend/src/**`

## Recommended PRD Direction

The PRD should decompose the work into small slices:

1. Add cycle persistence and closed-batch membership snapshot in SQLite/shared DB.
2. Adapt agent state machine for cycle start, pause, resume, completion, and idempotency.
3. Add reprocess/rearm semantics with audit/log trail.
4. Add Telegram notify-only support and dashboard relogin banner.
5. Add cycle API endpoints and schemas.
6. Rebuild dashboard navigation around tabs and cycle panel using React + Vite + shadcn/UI.
7. Replace existing UI primitives with shadcn/UI while preserving useful routes.
8. Add targeted tests and an assisted local Docker homologation script/checklist for 10 real processes.

## Validation Strategy

Required validation should include:

- Python unit/integration tests for cycle creation, membership snapshot, rearm, pause/resume, and idempotency.
- API tests for cycle status/history and agent control.
- Frontend tests for tabs, theme toggle, cycle table actions, and relogin banner.
- Telegram sender tests using mocked HTTP.
- Local Docker smoke test for API/frontend/agente startup.
- Assisted homologation with 10 real PJE/SISTJWEB processes, recording total time, per-process time, bottlenecks, and final outcomes.
