# MEMORY — CTO

> Arquivo dinâmico. Consulte antes de qualquer planejamento para manter
> consistência arquitetural entre sessões.

---

## Stack atual do projeto

- **Linguagem:** Python 3.12 (agente + API), TypeScript/React 18 (frontend)
- **Framework:** FastAPI 0.111 (API), React Router v6 (frontend)
- **Banco:** SQLite (migração para PostgreSQL 15 planejada — Wave 8)
- **Autenticação:** JWT via `python-jose` + `passlib` (migração para httpOnly cookies — Wave 3)
- **Testes:** pytest (agente), TestClient (API), Vitest + RTL + MSW (frontend — Wave 5)
- **Infra:** Docker Compose + Nginx (multi-stage build frontend). **Decisão atual:** todos os componentes, incluindo o agente, devem rodar em Docker local. O agente deve ser serviço longo, sem cron, acionado pelo dashboard, com navegador interativo exposto pelo container para SSO/2FA.

---

## Decisões arquiteturais

<!-- Nunca delete — apenas adicione. -->

- **2026-05-19 | Wave 4 da integração PJe/SISTJWEB: stale detection + cancelamento cooperativo + reautenticação explícita**
  Decidido: (1) tarefas `executando` há mais de 5 minutos são reenfileiradas automaticamente nos endpoints de leitura; (2) cancelamento agora aceita tarefas `pendente` e `executando`, marcando-as como `cancelado`; (3) `concluir_tarefa()` não sobrescreve tarefas canceladas; (4) tarefas `reautenticar_*` forçam navegador visível por intenção explícita do operador.
  Motivo: fecha os requisitos operacionais da Wave 4 sem adicionar broker, interrupção forçada de Playwright ou processo auxiliar de watchdog.
  Reversibilidade: média — o comportamento está concentrado em `sog_shared.db`, rotas de leitura e executor do agente.

- **2026-05-29 | Operação local totalmente containerizada**
  Decidido: (1) O agente deve permanecer no Docker Compose; (2) cron/VPS continuam fora do modelo operacional; (3) o agente roda como serviço longo dentro do container; (4) o botão `Iniciar Agente` no dashboard apenas envia o comando, enquanto o processo do agente já deve estar ativo no container; (5) SSO/2FA deve ocorrer em navegador interativo containerizado, exposto ao operador por noVNC ou mecanismo equivalente; (6) `storage_state` deve ficar em volume persistente controlado pelo Compose.
  Motivo: reduzir variação do ambiente local, evitar contaminação do host e manter todo o runtime reproduzível em Docker.
  Reversibilidade: média — substitui a decisão anterior de agente no host, mas preserva o modelo de serviço longo, SQLite como canal de comando/status e autenticação por `storage_state`.

- **2026-05-18 | Comunicação Backend ↔ Agente: fila de tarefas via SQLite (`agente_tarefas`)**
  Decidido: (1) Criar tabela `agente_tarefas` com `tipo`, `payload` JSON, `status`, `resultado` JSON, `sistema_alvo`; (2) Backend insere tarefa e retorna `task_id` (async job); frontend acompanha via polling em `GET /tarefas/{id}`; (3) Agente consome tarefas pendentes entre iterações do pipeline automático (máximo 3/iteração), usando lock em memória por sistema (`pje`/`sistj`/`ambos`); (4) Pipeline automático continua inalterado no loop principal; tarefas têm prioridade mas não causam starvation (limite por iteração).
  Alternativas: WebSocket (rejeitado — requer servidor WS no agente, complica firewall); HTTP polling agente→API (rejeitado — inverte dependência, requer retry/circuit breaker); RabbitMQ/Redis (rejeitado — nova infra, overkill para <10 req/min).
  Motivo: SQLite como canal de comunicação é o menor salto evolutivo da arquitetura atual (já compartilhado, WAL mode suporta concorrência, BEGIN IMMEDIATE garante atomicidade). Não introduz dependências externas. Fila persistente permite rastreabilidade e audit trail.
  Reversibilidade: **média** — tabela `agente_tarefas` é aditiva (não altera existentes), mas uma vez populada requer migração/truncamento para remoção. Lock em memória é fácil de migrar para lock no banco se agente for distribuído no futuro.

- **2026-05-17 | Agente: script de execução única → serviço longo (daemon)**
  Decidido: (1) Agente passa a rodar como processo longo com loop infinito (coleta → preenche → emite → dorme 30s → repete); (2) Comunicação bidirecional entre dashboard e agente via tabela `agente_controle` no SQLite (API escreve `comando`, agente escreve `status`); (3) Graceful shutdown via signal handlers (SIGINT/SIGTERM) com `threading.Event`; (4) Emissão pós-aprovação integrada no loop síncrono (não mais BackgroundTasks nem script separado).
  Alternativas: Agente como script executado pelo dashboard via subprocess (impossível — API está em container, agente no host); WebSocket entre agente e API (overkill — requer servidor HTTP no agente); file watcher (frágil — sem garantia de entrega).
  Motivo: O modelo de script único exige cron ou execução manual repetida, o que é incompatível com autenticação interativa (o operador não pode ficar digitando senha a cada 30 minutos). Serviço longo permite que o operador faça login uma vez pela manhã e o agente trabalhe o dia inteiro. SQLite como canal de comunicação é o mecanismo mais simples e confiável dado que ambos já compartilham o banco.
  Reversibilidade: **baixa** — altera o entry point do agente (`main.py` → `servico.py`), remove cron, muda modelo de emissão, e introduz máquina de estados. Rollback requer restaurar `main.py` como entry point, reintroduzir cron, e restaurar `BackgroundTasks` na API.

- **2026-05-17 | Autenticação: SSO Microsoft + 2FA → Operação local com Storage State**
  Decidido: (1) Agente passa a operar no host nativo (fora do Docker) para acesso ao display e Chrome do operador; (2) Autenticação via Playwright Storage State persistente (`context.storage_state()`) como mecanismo primário, com fallback para navegador visível quando a sessão expirar; (3) Emissão pós-aprovação migrada da API para o agente via fila baseada em status do banco (`status='aprovado'` consumido pelo agente).
  Alternativas: `connect_over_cdp` com Chrome já aberto (rejeitado — UX ruim, conflito de perfis); login programático (impossível — Microsoft Authenticator não expõe secret TOTP); espera interativa a cada execução (rejeitado — bloqueia cron e UX péssima).
  Motivo: SSO Microsoft com 2FA via app móvel impossibilita qualquer login automatizado. A operação local com operador humano presente exige que o login seja feito por ele, mas pode ser reutilizado por horas via cookies de sessão. Rodar o agente no host elimina complexidade de X11/VNC no Docker.
  Reversibilidade: **baixa** — altera arquitetura de deploy (agente fora do container), remove BackgroundTasks da API, e remove cron como mecanismo primário. Rollback requer restaurar serviço `agente` no docker-compose, mover credenciais de volta para `.env.agente`, e reintroduzir emissão na API.
  **Status:** parcialmente superseded pela decisão de 2026-05-29. Mantêm-se SSO/2FA interativo e `storage_state`; substitui-se "agente no host" por "agente em Docker com navegador interativo containerizado".

- **2026-05-17 | Extrator PDF: correções P2 (double-close + scanned detection)**
  Decidido: (1) Remover `doc.close()` do `except`, mantendo apenas no `finally` de `extrair_texto_pdf()`; (2) Substituir heurística de scanned de "qualquer página" para heurística agregada: `proporcao_scanned > 0.8 and media_texto < 100`.
  Alternativas para scanned: manter página-a-página (falso positivo aceitável); usar apenas proporção; usar apenas média de texto.
  Motivo: Double-close é bug puro — `finally` já garante o close. Heurística agregada elimina falsos positivos em PDFs com capa image-only (brasão) sem perder detecção de PDFs 100% scanned.
  Reversibilidade: alta — thresholds (`0.8`, `100`) são constantes internas; ajustáveis sem quebrar contratos.

- **2026-05-17 | Extrator PDF: extração de custas iniciais**
  Decidido: Adicionar `extrair_custas_iniciais()` que reusa `extrair_texto_pdf()` + `extrair_documentos_capa()`, localiza guias pela ocorrência do `doc_id` no texto completo (janela de ±1500 chars) e aplica regex para extrair valor total, detalhamento, número da guia e vencimento.
  Alternativas: Extrair diretamente por coordenadas da página da guia; usar LLM para parse da guia.
  Motivo: Coordenadas são frágeis (variam entre PDFs); LLM é overkill e lento para um padrão bem definido. Busca por doc_id + janela + regex é determinística, rápida e testável.
  Reversibilidade: alta — feature puramente aditiva (novo campo no dict de retorno); remoção não quebra callers existentes.

- **2026-05-15 | Auth: JWT em localStorage → httpOnly cookies**
  Decidido: Migrar tokens de `localStorage` para `httpOnly Secure SameSite=Strict` cookies emitidos pelo backend.
  Alternativas: Manter localStorage + CSP strita; usar sessionStorage.
  Motivo: Eliminar vetor XSS completo contra tokens de sessão (OWASP A01:2021).
  Reversibilidade: média — requer sincronia frontend+backend para rollback.

- **2026-05-15 | Banco: SQLite → PostgreSQL**
  Decidido: SQLite em WAL mode como ponte (Wave 4); PostgreSQL 15 como destino final (Wave 8).
  Alternativas: Manter SQLite com WAL eternamente; usar PostgreSQL imediato.
  Motivo: Resolver race conditions (CR-004), permitir concorrência real entre agente e API, e atender requisitos de backup/HA.
  Reversibilidade: **baixa** — migração de dados é unidirecional sem rollback trivial.

- **2026-05-15 | Pacote compartilhado `shared/`**
  Decidido: Extrair `db.py`, schemas Pydantic e config para pacote Python próprio (`shared/sog_shared/`).
  Alternativas: Manter `sys.path.insert` + cópia de código; usar submodules git.
  Motivo: Eliminar acoplamento crítico Agente→API (CR-008), permitir versionamento independente.
  Reversibilidade: alta — rollback via restauração de PYTHONPATH e cópia de arquivos.

- **2026-05-15 | Rate limiting: slowapi (memória)**
  Decidido: Usar `slowapi` com limitador em memória para MVP.
  Alternativas: Redis + fastapi-limiter; nginx limit_req sozinho.
  Motivo: Evitar dependência infra extra (Redis) antes do PostgreSQL; nginx limit_req complementa como camada externa.
  Reversibilidade: alta — substituir por Redis futuramente sem mudar contratos.

- **2026-05-15 | UX Dashboard: Filtros client-side no histórico**
  Decidido: Implementar filtros de histórico client-side inicialmente (status, data, valor).
  Alternativas: Filtros server-side via query params no `/historico`.
  Motivo: Endpoint não suporta filtros hoje; client-side é trivial e totalmente reversível. Migração para server-side não quebra UI.
  Reversibilidade: alta — só requer mover lógica de filtro para query string.

- **2026-05-15 | UX Dashboard: Threshold de valor alto hardcoded**
  Decidido: Threshold de "valor muito alto" = R$ 50.000,00 hardcoded no frontend.
  Alternativas: Campo configurável no banco (`config` table); variável de ambiente.
  Motivo: Não existe mecanismo de configuração no banco atual; valor pode ser extraído para config futura sem quebrar contrato.
  Reversibilidade: alta — alterar constante em `lib/formatters.ts` ou migrar para config dinâmica.

- **2026-05-15 | UX Dashboard: Status de emissão usa `erro` (não `erro_emissao`)**
  Decidido: O frontend trata status `erro` como falha na emissão.
  Alternativas: Alterar emissor.py para usar `erro_emissao`; criar estado intermediário.
  Motivo: Schema do banco e emissor usam `erro`. O TODO_frontend.md menciona `erro_emissao` incorretamente.
  Reversibilidade: alta — se `erro_emissao` for introduzido no futuro, basta adicionar ao enum de status.

- **2026-05-16 | Script utilitário de extração de sentença de PDF**
  Decidido: `pymupdf` (fitz) para extração de texto com análise de layout; script em `tools/testar_pdf.py` na raiz; heurística regex para isolar DISPOSITIVO (`ANTE O EXPOSTO`/`DISPOSITIVO`/`DECIDO`); detecção de PDF scanned via `get_text()` + presença de imagens.
  Alternativas: `pdfplumber` (MIT) — mais lenta, sem vantagem de layout para este caso; colocar script dentro de `agente/tools/` — reforça acoplamento com runtime.
  Motivo: PyMuPDF oferece extração por blocos (melhor para localizar dispositivo) e detecção nativa de scanned; script em raiz indica claramente que é ferramenta de dev/teste.
  Reversibilidade: alta para localização e heurística; **média** para biblioteca (AGPL-3.0) — trocar por `pdfplumber` requer apenas refatorar a função de extração de texto, pois o script isola a lib.

---

## Padrões do projeto

- Imports absolutos a partir de `src/` no frontend; imports de pacote `sog_shared` no Python.
- Variáveis de ambiente via `python-dotenv` no agente; lifespan do FastAPI para validação no startup da API.
- Logs estruturados em JSON (`agente/src/utils/logger.py` — positive finding).
- Queries SQLite parametrizadas com `?` placeholders (positive finding).
- Tokens JWT com claims `iss`, `aud`, `iat`, `exp`, `sub`, `type` (a partir de Wave 3).
- Parser de valor monetário deve ser extraído para `frontend/src/lib/formatters.ts` para reuso entre W2-F9 e W3-F13.

---

## Débitos técnicos identificados

- `api/src/auth.py:19`: JWT secret derivado de hash bcrypt com fallback hardcoded — **bloqueia deploy** (CR-003).
- `docker-compose.yml:59`: Volume de screenshots exposto no nginx sem autenticação — **bloqueia deploy** (CR-005).
- `agente/src/banco/db.py:174`: `_init_db()` executa no import global — causa side-effects e dificulta testes (M-012). **Nota:** `sog_shared/db.py` já corrigiu isso; verificar se `agente/src/banco/db.py` ainda existe ou foi consolidado.
- `api/src/rotas/aprovacao.py:50`: Race condition entre SELECT e UPDATE em conexões diferentes — **bloqueia deploy** (CR-004). **Nota:** Corrigido em `sog_shared/db.py` com `get_conn()` + `BEGIN IMMEDIATE`; verificar se API ainda usa padrão antigo em algum lugar.
- `frontend/src/lib/api.ts:8`: Tokens em `localStorage` — vetor XSS (CR-006).
- `api/src/rotas/auth.py:39-55`: Refresh token reutilizável infinitamente — **bloqueia deploy** (CR-014).
- `agente/src/modulos/pje.py:120-128`: Seletores CSS interpolados sem escaping — **bloqueia deploy** (CR-002). **Nota:** Parcialmente corrigido com `escape_for_css`, mas templates em `selectors.py` e uso de `.format()` em `sistjweb.py` ainda precisam de auditoria completa.
- **Novo (2026-05-17)**: Emissão pós-aprovação quebrada — API importa `modulos.emissor` que não existe no container API. **Plano de correção:** `.kimi/plans/agente-servico-longo.md` Fase 1 + Fase 2.
- **Novo (2026-05-15)**: Endpoint `/historico` não suporta filtros server-side — pode virar gargalo se histórico > 500 registros (mitigação: filtros client-side por enquanto).
- **Novo (2026-05-15)**: Endpoint `/historico/exportar` (CSV) não existe — precisa ser criado na Wave 3 (W3-F14).

---

## Planos executados (índice)

- `.kimi/context/cto/code-review-fixes.md` — Plano técnico para 98 issues do code review enterprise (2026-05-15)
- `.kimi/context/cto/todo-frontend.md` — Plano técnico para 14 features de UX do dashboard, decomposto em 3 waves (2026-05-15)
- `.kimi/plans/extrator-pdf.md` — Plano técnico para script utilitário de extração de sentença de PDF (2026-05-16)
- `.kimi/plans/extracao-custas-iniciais.md` — Plano técnico para extração de valor das custas iniciais de PDF judicial (2026-05-17)
- `.kimi/plans/correcoes-p2-extrator-pdf.md` — Plano técnico para correções P2 no extrator de PDF (double-close + scanned detection) (2026-05-17)
- `.kimi/plans/adaptacao-sso-2fa.md` — Plano técnico para adaptação a SSO Microsoft + 2FA (arquitetura de script única — **SUPERSEDED** por `agente-servico-longo.md`) (2026-05-17)
- `.kimi/plans/agente-servico-longo.md` — Plano técnico para agente como serviço longo (daemon), comunicação via SQLite, autenticação storage state, emissão em tempo real, e dashboard de controle (2026-05-17)
- `.kimi/plans/integracao-pje-sistjweb.md` — Plano técnico para integração completa backend↔agente: fila de tarefas SQLite, comandos parametrizados, ações sob demanda em PJe/SISTJWEB, dashboard de sessões (2026-05-18)
