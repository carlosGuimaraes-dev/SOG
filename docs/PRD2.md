# PRD Complementar — Refatoração local no-overengineering do SOG

Status: ready-for-agent

Fonte:

- `CONTEXT.md`
- `docs/no-overengineering-elicitation.md`
- Relatório arquitetural temporário: `/private/tmp/architecture-review-20260602-213457.html`

## Problem Statement

O SOG ainda carrega decisões arquiteturais que contradizem o produto aprovado
para o escopo atual. O sistema deve ser uma ferramenta local assistida para um
operador Windows leigo, mas o runtime ainda expõe ou preserva conceitos de
dashboard autenticado, painel Electron, Docker Desktop como jornada, cópias de
schema/modelos e uma metodologia frágil de login externo baseada em copiar
sessão de navegador.

O problema mais urgente para o operador é o login manual externo em PJe e
SISTJWEB. Hoje o SOG abre múltiplas instâncias de Chromium, fecha antes do 2FA
ser concluído e tenta transferir `storage_state` para outro navegador. Na
prática, o operador faz login nas plataformas externas e mesmo assim o agente
não consegue operar. Isso quebra o fluxo central do SOG.

O segundo problema é a experiência de instalação/operação. O operador não deve
entender Node.js, npm, Docker CLI, Docker Desktop, WSL, Compose, terminal ou
caminhos locais. O executável deve entregar o SOG pronto, pedir autorização
quando precisar preparar runtime interno e oferecer diagnóstico simples para
suporte quando algo não puder ser resolvido automaticamente.

O terceiro problema é arquitetural: contratos compartilhados e responsabilidades
de domínio estão duplicados ou misturados. Isso aumenta drift, dificulta testes
e torna o código menos navegável para agentes e humanos.

## Solution

Refatorar o SOG para alinhar código, runtime e documentação ao modelo aprovado:
ferramenta local assistida, sem login do dashboard, com Electron apenas como
casca local, dashboard principal como experiência operacional única, e login
manual externo feito em um Navegador de sessão do SOG persistente.

O operador usará uma aba de configuração dentro do dashboard principal. Nela,
terá ações independentes para abrir PJe e SISTJWEB no Navegador de sessão do
SOG. O operador fará login e 2FA nesses sistemas sem pressa. O agente validará
cada sessão separadamente e operará na mesma sessão original. O fluxo de copiar
`storage_state` para outro navegador deixará de ser o mecanismo principal.

O executável preparará runtime interno de forma automatizada. Ele verificará
Node.js, npm, Docker CLI e WSL. Quando algo faltar, pedirá autorização na
interface, explicará elevação/UAC quando necessário e retomará após
reinicialização do Windows quando for inevitável. Docker Desktop não será a via
operacional do usuário final.

O contrato compartilhado será consolidado em `shared/sog_shared`. A API poderá
ter contratos de apresentação, o frontend poderá ter modelos de tela, mas
nenhuma camada deve redefinir domínio compartilhado. O banco compartilhado será
organizado por fronteiras de domínio, sem criar camada repository especulativa.

## User Stories

1. As an operador, I want to install SOG from an executable, so that I do not need to learn terminal commands.
2. As an operador, I want SOG to check required runtime dependencies for me, so that I do not need to know what Node.js, npm, Docker CLI, WSL or Compose are.
3. As an operador, I want SOG to ask permission before installing missing runtime dependencies, so that I understand when my machine is being changed.
4. As an operador, I want SOG to explain Windows elevation prompts before they appear, so that UAC is not surprising.
5. As an operador, I want SOG to resume installation after a required Windows restart, so that I do not need to restart the setup manually.
6. As an operador, I want support contact details when installation cannot continue, so that I know who to call or email.
7. As an operador, I want the dashboard to be the only operational surface, so that I do not need to understand a separate Electron panel.
8. As an operador, I want configuration to live in a dashboard tab, so that setup and operation happen in one familiar place.
9. As an operador, I want a button to open PJe, so that I can authenticate in the external system when needed.
10. As an operador, I want a separate button to open SISTJWEB, so that I can authenticate it independently from PJe.
11. As an operador, I want PJe and SISTJWEB login windows to stay open, so that I have enough time for SSO and 2FA.
12. As an operador, I want SOG to validate the PJe session separately, so that a SISTJWEB problem does not block PJe status.
13. As an operador, I want SOG to validate the SISTJWEB session separately, so that a PJe problem does not block SISTJWEB status.
14. As an operador, I want the agent to use the session where I actually logged in, so that login works reliably.
15. As an operador, I want SOG to avoid storing my PJe or SISTJWEB password, so that external credentials remain private.
16. As an operador, I want clear status when a login is pending, so that I know what action is required.
17. As an operador, I want clear status when both external sessions are active, so that I know the agent can continue.
18. As an operador, I want the dashboard to show operational state rather than a technical job queue, so that I can focus on work.
19. As an operador, I want approval actions to remain explicit, so that sensitive actions do not continue without my decision.
20. As an operador, I want reauthentication to be guided from the dashboard, so that expired sessions can be fixed without terminal access.
21. As an operador, I want SOG to keep local operational traceability, so that support can understand what happened.
22. As an operador, I want the executable to prepare local installation automatically, so that setup does not depend on Docker Desktop.
23. As an operador, I want Docker Desktop not to be part of my workflow, so that I do not need Docker knowledge.
24. As support, I want technical diagnostics when runtime preparation fails, so that I can troubleshoot without asking the operador to interpret stack traces.
25. As support, I want diagnostics to include the failing runtime step, so that I can distinguish Node.js, npm, Docker CLI, WSL and container startup failures.
26. As support, I want PJe and SISTJWEB session status to be independent, so that I can diagnose one external system without confusing it with the other.
27. As support, I want the agent to use a persistent SOG browser profile, so that session problems are reproducible.
28. As a developer, I want the Navegador de sessão do SOG module to hide browser/session mechanics, so that callers do not coordinate CDP, storage files and Playwright contexts.
29. As a developer, I want to delete copied-session choreography, so that login bugs stop spreading across desktop, agent and service loop code.
30. As a developer, I want Electron to be a casca local only, so that operational UI changes happen in the dashboard.
31. As a developer, I want dashboard configuration to be testable without Electron UI, so that configuration behavior has faster feedback.
32. As a developer, I want `shared/sog_shared` to own the Contrato compartilhado, so that schema/model drift is removed.
33. As a developer, I want API contracts of presentation to be distinct from domain contracts, so that route-specific formatting does not become a second domain model.
34. As a developer, I want frontend models of tela to be presentation-only, so that UI convenience does not redefine domain behavior.
35. As a developer, I want tests to use the shared schema, so that API and agent tests exercise the same Banco compartilhado.
36. As a developer, I want the banco compartilhado implementation organized by fronteira de domínio, so that changes in cycles do not require understanding approval SQL.
37. As a developer, I want to avoid repository layers for a single SQLite source, so that the refactor does not replace one complexity with another.
38. As a developer, I want dead dashboard-auth code removed, so that future agents do not preserve a nonexistent requirement.
39. As a developer, I want no mode exposto in this PRD, so that local scope stays focused.
40. As a developer, I want retained complexity to be explicit, so that Playwright per system, SQLite transactions and dashboard sections are not mistakenly removed.
41. As a product owner, I want implementation to prioritize the broken login path first, so that the highest-impact operator problem is resolved early.
42. As a product owner, I want the PRD to preserve deferred items, so that multiuser, exposed mode and per-person audit are not accidentally added now.

## Implementation Decisions

- The SOG remains a Ferramenta local assistida. It is not a multiuser product in this PRD.
- The Dashboard local has no login próprio. Dashboard JWT, refresh token, user identity and related auth concepts are removed from the local runtime.
- Login manual externo remains required for PJe and SISTJWEB. SOG must not store external passwords.
- The Navegador de sessão do SOG is the top-priority deep module. Its interface should cover opening PJe, opening SISTJWEB, validating each session and allowing the agent to operate in the original session.
- The existing copied-session mechanism is deleted as the main path. The agent should not rely on exporting/importing `storage_state` into a separate browser to operate after login.
- PJe and SISTJWEB opening and validation are independent. There is no single coupled login button for both systems.
- The operator must have enough time for SSO/2FA. The SOG must not close the login browser because a short automation timeout elapsed.
- Electron becomes Casca local. It prepares runtime and opens the dashboard; it does not own a permanent operational panel.
- Configuração operacional moves into an Aba de configuração in the dashboard principal.
- Runtime interno preparation belongs to the executable/local shell, not to the operador. The executable checks Node.js, npm, Docker CLI and WSL.
- When runtime dependencies are absent, the executable asks for Autorização de instalação local and continues preparation.
- When Windows requires elevation, the SOG uses Elevação explicada before triggering UAC.
- When Windows requires restart, the SOG uses Retomada após reinicialização and preserves installation state.
- Docker CLI automatizado is the preferred operational path. Docker Desktop is not a user journey.
- Diagnóstico para suporte must show a simple operator-facing message plus telephone/email contact details and preserve technical detail for support.
- `npx`/R2 remains an Atalho técnico de distribuição, not the primary operador journey.
- `shared/sog_shared` is the canonical Contrato compartilhado and owner of Banco compartilhado schema.
- API-specific response shapes are Contratos de apresentação da API and must not redefine shared domain language.
- Frontend-specific shapes are Modelos de tela and must not redefine shared domain language or API contracts.
- Duplicação de domínio is removed. Presentation-specific duplication can remain only when it is explicitly presentation.
- The banco compartilhado implementation should be organized by Fronteira de domínio: Processos e aprovação, Agente e ciclos, Tarefas e sessões externas, and Infraestrutura de banco.
- The database refactor must avoid speculative repository classes. The database has one concrete source today: local SQLite.
- Tarefa operacional remains part of the domain, but the dashboard presents Estado operacional, not a technical queue administration surface.
- Playwright modularization by external system is retained when PJe and SISTJWEB flows, selectors, downloads and timeouts differ.
- SQLite shared transactions are retained for Concorrência local controlada.
- Dashboard por seções is retained as long as sections do not duplicate domain contracts.
- Modo exposto, multiuser, per-person audit, Docker Desktop journey and capturing arbitrary uncontrolled Chrome sessions are out of scope.

## Testing Decisions

- Tests should verify external behavior at module interfaces, not internal implementation details.
- The best tests for the Navegador de sessão do SOG verify behavior through the session module interface: open PJe, open SISTJWEB, validate PJe, validate SISTJWEB, and reuse original session.
- Session tests should prove PJe validation does not depend on SISTJWEB validation and vice versa.
- Tests should prove the login browser remains available for manual 2FA and is not closed by the automation path.
- Tests should prove no PJe/SISTJWEB password is persisted.
- Dashboard tests should prove the local dashboard opens without login and does not redirect to `/login`.
- API tests should prove local dashboard routes do not require JWT or refresh tokens.
- Configuration tests should exercise the Aba de configuração as the operator-facing surface.
- Runtime preparation tests should cover missing Node.js, missing npm, missing Docker CLI and missing/disabled WSL as distinct outcomes.
- Runtime preparation tests should prove the user is asked before local installation/configuration steps continue.
- Runtime preparation tests should prove elevation messaging is shown before UAC-triggering operations.
- Runtime preparation tests should prove reboot-needed state can be resumed.
- Support diagnostic tests should prove operator-facing messages include telephone/email and preserve technical detail for support.
- Contract tests should prove API and agent tests use the schema from the Contrato compartilhado.
- Shared model tests should prove duplicated domain schemas/models are not reintroduced.
- Frontend tests should distinguish Modelo de tela from API/domain contracts by checking rendered behavior rather than copying backend types.
- Banco compartilhado tests should target behavior by Fronteira de domínio rather than SQL implementation details.
- Existing test prior art includes API route tests, agent service tests, frontend page/component tests, and desktop package verification scripts.

## Out of Scope

- Modo exposto/remoto.
- Multiuser dashboard.
- Per-person audit in the dashboard.
- Dashboard login.
- JWT/refresh-token authentication for local dashboard.
- Docker Desktop as the operator workflow.
- Technical queue administration by the operator.
- Capturing any arbitrary Chrome instance already opened outside SOG control.
- Replacing SQLite with another database.
- Introducing repository/service/factory layers just for architectural neatness.
- Rewriting Playwright automation for PJe/SISTJWEB beyond what is needed to make the approved session strategy work.
- Creating a formal ADR before this PRD is reviewed and converted into implementation issues.

## Further Notes

- This PRD is complementary to the historical `docs/PRD.md`; it supersedes conflicting assumptions about dashboard login, Docker Desktop as operator journey, and Electron as an operational panel.
- The approved elicitation is in `docs/no-overengineering-elicitation.md`.
- The domain glossary is in `CONTEXT.md` and should be treated as the vocabulary source for future issues.
- Top implementation recommendation: begin with the Navegador de sessão do SOG because it fixes the current broken operator path and deletes the fragile copied-session process.
- The architecture report generated during elicitation is `/private/tmp/architecture-review-20260602-213457.html`.
- Issue breakdown for Paperclip lives in `docs/paperclip/no-overengineering-runtime-refactor/issues/`.
