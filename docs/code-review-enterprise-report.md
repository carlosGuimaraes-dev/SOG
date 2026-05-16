# Enterprise Code Review Report
## SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)

**Data:** 2026-05-15  
**Classificação:** CONFIDENCIAL — Uso Interno  
**Versão:** 1.0  
**Metodologia:** Code review em 4 waves cobrindo ~45 artefatos de código, infraestrutura e configuração.

---

## 1. Executive Summary

### 1.1 Visão Geral

O SOG é um pipeline de automação para extração, preenchimento e emissão de guias de custas processuais no TJDFT. A arquitetura consiste em três camadas:

| Camada | Tecnologia | Responsabilidade |
|--------|-----------|------------------|
| Agente | Python 3.12 + Playwright | Automação PJE/SISTJWEB + API Datajud CNJ |
| API | FastAPI + SQLite + JWT | Backend do dashboard de aprovação |
| Frontend | React 18 + Vite + Tailwind CSS | Dashboard de revisão humana |
| Infra | Docker Compose + Nginx | Orquestração e proxy reverso |

### 1.2 Scorecards por Módulo

| Módulo | Arquivos | Issues | 🔴 Crítico | 🟠 Alto | 🟡 Médio | 🟢 Baixo | Score |
|--------|----------|--------|-----------|--------|----------|----------|-------|
| Agente (Python) | 21 | 25 | 2 | 8 | 10 | 5 | **6.5/10** |
| API (FastAPI) | 10 | 22 | 3 | 9 | 6 | 4 | **4.0/10** |
| Frontend (React) | 16 | 21 | 3 | 10 | 6 | 2 | **4.0/10** |
| Cross-cutting (Infra) | 14 | 30 | 7 | 11 | 7 | 5 | **3.5/10** |
| **Total** | **61** | **98** | **15** | **38** | **29** | **16** | **4.5/10** |

### 1.3 Veredicto Global

> **REPROVADO para deploy em produção.**

Existem **15 issues classificadas como CRÍTICAS** que impossibilitam o deploy em ambiente que toque dados reais do TJDFT. Os bloqueadores concentram-se em:

1. **Segurança da autenticação:** JWT secret previsível/backdoor de login.
2. **Exposição de dados sensíveis:** screenshots de processos judiciais acessíveis sem autenticação.
3. **Integridade de dados:** race conditions em aprovação + SQLite compartilhado sem controle de concorrência.
4. **Vulnerabilidades de injeção:** SQL estrutural + seletores CSS interpolados sem escaping.
5. **Armazenamento inseguro de tokens:** JWT em `localStorage` (XSS).

Após correção dos bloqueadores e das issues de severidade ALTA, o sistema pode ser reavaliado para **APROVADO COM RESSALVAS**.

---

## 2. Risk Heat Map

| Categoria de Risco | Agente | API | Frontend | Infra | Total Crítico |
|-------------------|--------|-----|----------|-------|---------------|
| **Segurança / Auth** | 1 | 3 | 2 | 3 | **9** |
| **Segurança / Dados** | 2 | 0 | 0 | 2 | **4** |
| **Integridade / Concorrência** | 0 | 1 | 0 | 1 | **2** |
| **Injeção (SQL/CSS)** | 2 | 1 | 0 | 0 | **3** |
| **Confidencialidade / LGPD** | 1 | 0 | 0 | 1 | **2** |

---

## 3. Critical Issues (🔴) — Deduplicados e Consolidados

### CR-001 — SQL Injection Estrutural no SQLite
- **Arquivos:** `agente/src/banco/db.py:93-110`, `api/src/rotas/aprovacao.py` (via db.py)
- **Linhas:** 93-110
- **Categoria:** Segurança / Injeção
- **Descrição:** A função `salvar_dados_processo` monta dinamicamente a query INSERT interpolando nomes de colunas via f-string (`f"INSERT ... ({colunas}) ..."`). Os valores usam placeholders `?`, mas os nomes das colunas vêm de `dados.keys()` sem whitelist nem validação.
- **Impacto de Negócio:** Se o payload de dados incluir chaves controladas por entrada externa, permite manipulação do schema do banco e potencial SQL injection estrutural. Em um sistema que lida com valores de causa processual, isso pode comprometer a integridade financeira dos cálculos.
- **Recomendação:** Manter uma whitelist explícita das colunas permitidas do schema `dados_processo`. Validar `campos` contra essa lista antes de concatenar a query. Rejeitar campos desconhecidos com erro explícito.
- **Módulos afetados:** Agente, API
- **Referência:** CWE-89, OWASP A03:2021

---

### CR-002 — Injeção em Seletores CSS do Playwright
- **Arquivos:** `agente/src/modulos/pje.py:120-128`, `agente/src/modulos/sistjweb.py:464`
- **Categoria:** Segurança / Injeção
- **Descrição:** Funções como `_clicar_por_texto_exato` e `sistjweb.py` interpolam texto cru em seletores CSS do tipo `f"text='{texto}'"`. Se o número do processo, etiqueta ou nome do documento contiver aspas simples (`'`), o seletor quebra sintaticamente.
- **Impacto de Negócio:** Falha irreversível na automação para processos com apóstrofos nos nomes das partes. Em escala, pode deixar processos pendentes indefinidamente, acumulando backlog operacional.
- **Recomendação:** Substituir por APIs semânticas do Playwright (`page.get_by_text(texto, exact=True).click()`) que tratam escapamento internamente. Criar helper `escape_for_selector()` como camada de proteção adicional.
- **Módulos afetados:** Agente
- **Referência:** CWE-94

---

### CR-003 — JWT Secret Comprometido / Backdoor de Autenticação
- **Arquivos:** `api/src/auth.py:19`, `api/src/auth.py:95-101`, `.env.example`
- **Categoria:** Segurança / Auth
- **Descrição:** (a) `SECRET_KEY` é derivado de `DASHBOARD_SENHA_HASH` (hash bcrypt, inadequado para HMAC) com fallback hardcoded `"dev-secret-change-in-production"`. (b) `authenticate_user` retorna `True` para qualquer senha quando o hash está ausente/inválido.
- **Impacto de Negócio:** Comprometimento total da autenticação. Se o `.env` não for configurado corretamente em produção, qualquer pessoa obtém token de acesso e pode aprovar/rejeitar guias de custas em nome de operadores legítimos. Risco financeiro e legal de emissão indevida.
- **Recomendação:**
  1. Adicionar envvar separada `JWT_SECRET_KEY` com valor aleatório de ≥256 bits (`secrets.token_hex(32)`).
  2. Remover fallback hardcoded; a aplicação deve falhar no startup se `JWT_SECRET_KEY` estiver ausente.
  3. Remover modo "dev sem senha"; validação do hash deve ocorrer no startup, não no login.
- **Módulos afetados:** API
- **Referência:** CWE-798, OWASP A02:2021, CWE-287

---

### CR-004 — Race Condition em Aprovação de Guias
- **Arquivo:** `api/src/rotas/aprovacao.py:36-55`, `docker-compose.yml:11,27`
- **Categoria:** Integridade / Concorrência
- **Descrição:** O status do processo é verificado em uma conexão SQLite (`with db.get_conn()`), mas a atualização (`db.atualizar_status`) abre uma nova conexão independente. Não há transação atômica nem `BEGIN IMMEDIATE`. O SQLite compartilhado via volume entre agente e API agrava o problema.
- **Impacto de Negócio:** Dupla aprovação do mesmo processo, dupla emissão de guia de custas, possível prejuízo financeiro duplicado. Inconsistência de estado no banco que pode levar a divergências entre o dashboard e o SISTJWEB.
- **Recomendação:**
  1. Imediato: usar uma única transação atômica dentro do mesmo `with db.get_conn() as conn`, com `BEGIN IMMEDIATE`.
  2. Médio prazo: migrar para PostgreSQL com controle de concorrência nativo.
  3. Adicionar constraint UNIQUE ou status machine no banco para prevenir transições inválidas.
- **Módulos afetados:** API, Infra
- **Referência:** CWE-362

---

### CR-005 — Exposição Pública de Screenshots com Dados Judiciais
- **Arquivo:** `docker-compose.yml:59`
- **Categoria:** Segurança / Dados — LGPD
- **Descrição:** O volume `./dados/screenshots:/usr/share/nginx/html/screenshots:ro` expõe screenshots de processos judiciais diretamente pelo nginx, sem autenticação. As imagens contêm dados pessoais (nomes, CPF/CNPJ, valores) e informações processuais sensíveis.
- **Impacto de Negócio:** Violação grave da LGPD (art. 46, 50). Qualquer pessoa com acesso à URL pode visualizar documentos sensíveis. Risco de sanção administrativa do ANPD e processos cíveis por vazamento de dados de partes processuais.
- **Recomendação:**
  1. Remover o volume de screenshots do nginx imediatamente.
  2. Servir imagens apenas via endpoint de API autenticada (`GET /api/screenshots/{id}`) com validação JWT.
  3. Adicionar verificação de ownership: o usuário só pode acessar screenshots de processos que está autorizado a visualizar.
- **Módulos afetados:** Infra, API
- **Referência:** LGPD Art. 46, 50; CWE-200

---

### CR-006 — Armazenamento Inseguro de Tokens JWT (XSS)
- **Arquivo:** `frontend/src/lib/api.ts:8,21-26,30-31`
- **Categoria:** Segurança / Auth
- **Descrição:** Tokens JWT (`access_token` e `refresh_token`) são armazenados em `localStorage`. Qualquer vulnerabilidade XSS — inclusive em dependências transitórias — permite roubo imediato via `localStorage.getItem()`.
- **Impacto de Negócio:** Comprometimento total de sessões de operadores. Atacante pode aprovar/rejeitar processos em nome de outro operador, acessar dados de processos judiciais e screenshots do SISTJWEB. Como o sistema lida com valores monetários, o impacto é financeiro direto.
- **Recomendação:**
  1. Migrar para **httpOnly + Secure + SameSite=Strict cookies** gerenciados pelo servidor (`Set-Cookie` no backend).
  2. Remover todo acesso a `localStorage` para tokens.
  3. Usar `credentials: 'include'` no cliente HTTP.
  4. O backend deve emitir cookies nas rotas `/auth/login` e `/auth/refresh`.
- **Módulos afetados:** Frontend, API
- **Referência:** OWASP A01:2021, CWE-1004

---

### CR-007 — API Exposta Diretamente na Internet
- **Arquivo:** `docker-compose.yml:28`
- **Categoria:** Segurança / Infra
- **Descrição:** A API FastAPI mapeia a porta `8000` no host (`"8000:8000"`), permitindo acesso direto que bypassa o proxy reverso (nginx) e seus controles de segurança.
- **Impacto de Negócio:** Exposição direta do backend anula camada de proteção do nginx (rate limiting futuro, WAF, headers de segurança). Aumenta superfície de ataque significativamente.
- **Recomendação:** Remover o mapeamento `8000:8000`. A API deve ser acessível **apenas** via rede interna do Compose (`api:8000`) pelo nginx.
- **Módulos afetados:** Infra
- **Referência:** CWE-419

---

### CR-008 — Acoplamento Crítico: Agente → API
- **Arquivo:** `api/Dockerfile:9`, `api/src/rotas/*.py` (linhas 4-7)
- **Categoria:** Arquitetura / Acoplamento
- **Descrição:** A API copia o código fonte do agente (`COPY agente/src/ ./agente_src/`) e cada rota faz `sys.path.insert(0, ...)` para importar `config` e `banco` do agente. Violação grave de separação de concerns.
- **Impacto de Negócio:** Impossível versionar a API independentemente. Testes quebram se `agente/src/` não estiver no filesystem. Mudanças no agente podem quebrar a API silenciosamente. Deploy se torna frágil e não determinístico.
- **Recomendação:**
  1. Extrair módulos compartilhados (`db.py`, schemas) para um pacote Python próprio (`shared/` ou `lib/`).
  2. Remover `COPY agente/src/` do Dockerfile da API.
  3. Usar `PYTHONPATH` adequado ou instalar como pacote editável (`pip install -e shared/`).
- **Módulos afetados:** API, Infra
- **Referência:** CWE-1108

---

### CR-009 — Container do Agente com Privilégios Excessivos
- **Arquivo:** `agente/Dockerfile:1-25`
- **Categoria:** Segurança / Infra
- **Descrição:** Container do agente roda como `root` (padrão da imagem `python:3.12-slim`) e instala `cron`, que é um daemon de escalonamento privilegiado. O CMD usa shell form (`python ... && cron -f`), que quebra se o primeiro comando falhar.
- **Impacto de Negócio:** Risco de privilege escalation dentro do container. Comprometimento do host se houver escape de container. O orquestrador pode rodar duas vezes (startup + cron), causando condições de corrida na automação.
- **Recomendação:**
  1. Adicionar `RUN useradd -m appuser && chown -R appuser:appuser /app /dados` e `USER appuser`.
  2. Substituir `cron` do sistema por `supercronic` (roda como usuário não-privilegiado).
  3. Alterar CMD para `CMD ["cron", "-f"]` (exec form) e garantir que `main.py` seja executado **apenas** pelo cron.
- **Módulos afetados:** Infra
- **Referência:** CWE-250

---

### CR-010 — Erro Silenciado no Refresh Token (Promise Pendente)
- **Arquivo:** `frontend/src/lib/api.ts:29-32`
- **Categoria:** Robustez / UX
- **Descrição:** No `catch` do refresh token, o erro é silenciado (`catch { ... }`) e executa `window.location.href = '/login'`, mas a Promise original **não é rejeitada nem resolvida**.
- **Impacto de Negócio:** Chamadas axios pendentes ficam em espera indefinida. Estados de `loading` nunca são desativados. O operador pode ficar com tela travada sem feedback, levando a duplo-clique em botões de aprovação e possível dupla emissão.
- **Recomendação:** Adicionar `return Promise.reject(error)` após o redirect no catch, garantindo que todos os callers recebam a rejeição.
- **Módulos afetados:** Frontend
- **Referência:** CWE-391

---

### CR-011 — Roteamento Aninhado Incorreto (react-router-dom v6)
- **Arquivo:** `frontend/src/App.tsx:82-96`
- **Categoria:** Arquitetura / Roteamento
- **Descrição:** Uso incorreto de `<Routes>` aninhado dentro de outro `<Routes>`. No react-router-dom v6, rotas filhas devem ser declaradas com `element={<Layout />}` + `<Outlet>` no pai.
- **Impacto de Negócio:** Comportamento de matching imprevisível. Rotas inexistentes podem não cair em 404 corretamente. Re-mounts desnecessários em navegação. Dificulta aplicação de guards de autenticação.
- **Recomendação:** Refatorar para padrão `Outlet`: uma única árvore de rotas com `<Route element={<RequireAuth><Layout /></RequireAuth>}>` contendo rotas filhas.
- **Módulos afetados:** Frontend
- **Referência:** N/A (bug de implementação)

---

### CR-012 — PII em Logs (Violação LGPD)
- **Arquivo:** `agente/src/main.py:52,66`
- **Categoria:** Compliance / LGPD
- **Descrição:** `db.registrar_log(..., str(dados_datajud))` e `str(dados_parser)` persistem dados pessoais completos (nome, CPF/CNPJ, valor da causa, endereço de partes) na tabela `log_execucao`.
- **Impacto de Negócio:** Violação do princípio de minimização da LGPD (art. 7, VI). Logs não devem conter PII não mascarado. Em caso de vazamento de banco, todos os logs expõem dados sensíveis.
- **Recomendação:** Logar apenas identificadores (`processo_id`) e status. Remover ou mascarar campos sensíveis antes de serializar (ex: `CPF: ***.***.***-**`).
- **Módulos afetados:** Agente
- **Referência:** LGPD Art. 7, VI; CWE-532

---

### CR-013 — SQLite Compartilhado sem Controle de Concorrência
- **Arquivo:** `docker-compose.yml:11,27`
- **Categoria:** Integridade / Arquitetura
- **Descrição:** O volume `./dados:/dados` compartilha o mesmo SQLite entre `agente` e `api`. SQLite não foi projetado para concorrência write-heavy entre processos distintos.
- **Impacto de Negócio:** Race conditions, corrupção de banco de dados, bottleneck de escalabilidade. A Wave 2 já identificou race condition específica na aprovação. Se o volume corromper, perde-se todo o histórico processual.
- **Recomendação:**
  1. Imediato: ativar WAL mode (`PRAGMA journal_mode=WAL`) e aumentar timeout de lock.
  2. Médio prazo: migrar para PostgreSQL em container separado.
- **Módulos afetados:** Infra
- **Referência:** CWE-362

---

### CR-014 — Refresh Token Reutilizável Infinitamente
- **Arquivo:** `api/src/rotas/auth.py:39-55`
- **Categoria:** Segurança / Auth
- **Descrição:** Refresh token é reutilizável infinitamente (dentro do prazo de 7 dias) sem rotação nem blacklist/revogação.
- **Impacto de Negócio:** Se um refresh token for roubado (via XSS, log leak, interceptação), o atacante mantém acesso indefinidamente até a expiração natural — sem possibilidade de revogação.
- **Recomendação:** Implementar refresh token rotation: ao usar um refresh token, invalidar o antigo e emitir novo par. Armazenar em tabela `refresh_tokens` com flag `revoked`.
- **Módulos afetados:** API
- **Referência:** OWASP A02:2021, CWE-798

---

### CR-015 — Ausência de `.dockerignore`
- **Arquivo:** *(projeto raiz)*
- **Categoria:** Segurança / Infra
- **Descrição:** Não existe `.dockerignore` no repositório. O build context inclui `.env`, `dados/`, `.git/`, `node_modules/`, etc.
- **Impacto de Negócio:** Secrets e dados sensíveis podem vazar para as layers da imagem Docker mesmo que não sejam explicitamente copiados (via cache ou acidente). Um atacante com acesso à imagem pode extrair `.env` do build context.
- **Recomendação:** Criar `.dockerignore` na raiz com: `**/.env*`, `dados/`, `**/.git`, `**/node_modules`, `**/__pycache__`.
- **Módulos afetados:** Infra
- **Referência:** CWE-200

---

## 4. High Issues (🟠) — Top 15 por Impacto

### HI-001 — CORS Excessivamente Permissivo
- **Arquivo:** `api/src/app.py:37-43`
- **Descrição:** `allow_origins=["*"]` + `allow_credentials=True` permite que qualquer site faça requests cross-origin com credenciais.
- **Impacto:** Vazamento de cookies/tokens para origens não confiáveis.
- **Recomendação:** Restringir `allow_origins` ao domínio exato via envvar. Em dev, usar whitelist explícita (`["http://localhost:3000"]`).

### HI-002 — Threading sem Controle de Lifecycle
- **Arquivo:** `api/src/rotas/aprovacao.py:22-33`
- **Descrição:** `_disparar_emissao` inicia `threading.Thread` daemon sem pool, timeout ou retry. Falhas são silenciadas.
- **Impacto:** Usuário recebe "Emissão em andamento" mas nada acontece; múltiplas threads podem estourar recursos.
- **Recomendação:** Usar `BackgroundTasks` do FastAPI ou fila de tarefas (Celery/RQ).

### HI-003 — Zero Testes no Frontend
- **Arquivo:** `frontend/src/` (todos)
- **Descrição:** Não há pasta `tests/` nem arquivos de teste no frontend.
- **Impacto:** Regressões não detectadas; bugs em `aprovar()` só seriam pegos em teste manual.
- **Recomendação:** Adicionar Vitest + React Testing Library + MSW. Meta: 60% nos fluxos críticos.

### HI-004 — Componente Detalhe.tsx com 328 Linhas
- **Arquivo:** `frontend/src/pages/Detalhe.tsx`
- **Descrição:** Mistura lógica de API, estado local, UI complexa e decisões de negócio.
- **Impacto:** Impossível testar aprovação/rejeição sem montar toda a árvore; alta chance de regressão.
- **Recomendação:** Extrair hooks (`useProcesso`, `useAprovar`) e sub-componentes.

### HI-005 — Ausência de Rate Limiting
- **Arquivo:** `api/src/app.py`, `api/src/rotas/auth.py`
- **Descrição:** Nenhum endpoint tem rate limiting. Login e aprovação estão desprotegidos.
- **Impacto:** Brute force de senha; spam de aprovações; DoS.
- **Recomendação:** Adicionar `slowapi` ou `fastapi-limiter` com Redis.

### HI-006 — Duplicação de Inicialização Playwright
- **Arquivo:** `agente/src/modulos/pje.py:195-209` + `sistjweb.py:185-198`
- **Descrição:** ~70% da lógica de inicialização é idêntica em ambos os módulos.
- **Impacto:** Mudança de viewport/headless precisa ser feita em 2 lugares; risco de divergência.
- **Recomendação:** Extrair classe base `PlaywrightClient`.

### HI-007 — Retry Genérico Capturando Exception
- **Arquivo:** `agente/src/modulos/retry.py:150-213`
- **Descrição:** `@retry_on_exception(exceptions=(Exception, PlaywrightTimeout))` captura `Exception` como padrão.
- **Impacto:** Erros de programação (`NameError`, `AttributeError`) disparam retry, escondendo bugs.
- **Recomendação:** Restringir a exceções específicas (`TimeoutError`, `ConnectionError`, `PlaywrightTimeout`).

### HI-008 — Ausência de Error Boundaries
- **Arquivo:** `frontend/src/App.tsx`
- **Descrição:** Nenhum Error Boundary protege a aplicação. Qualquer erro de renderização quebra tudo.
- **Impacto:** Tela branca; operador perde trabalho em andamento.
- **Recomendação:** Implementar `ErrorBoundary` de classe envolvendo `<Routes>`.

### HI-009 — PII em HTML de Email sem Escaping
- **Arquivo:** `agente/src/utils/notificador.py:25-27`
- **Descrição:** Dados de processos interpolados em template HTML sem `html.escape()`.
- **Impacto:** Injeção de conteúdo HTML no corpo do email.
- **Recomendação:** Escapar todos os valores com `html.escape()`.

### HI-010 — Containeres Rodando como Root
- **Arquivo:** Todos os Dockerfiles
- **Descrição:** Nenhum Dockerfile declara `USER` não-root.
- **Impacto:** Comprometimento do container = root no contexto, facilitando escape.
- **Recomendação:** Adicionar criação de usuário e `USER` em todos os Dockerfiles.

### HI-011 — Ausência de Security Headers no Nginx
- **Arquivo:** `nginx/nginx.conf`, `nginx/nginx-dev.conf`
- **Descrição:** Nenhum header de segurança HTTP é configurado.
- **Impacto:** Vulnerável a clickjacking, MIME-sniffing, XSS.
- **Recomendação:** Adicionar `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `HSTS`.

### HI-012 — Sem Paginação em /processos
- **Arquivo:** `api/src/rotas/processos.py:18-27`
- **Descrição:** Retorna todos os processos pendentes + manuais de uma vez.
- **Impacto:** Se o volume crescer, pode estourar memória do worker ou causar timeout.
- **Recomendação:** Adicionar `limit`/`offset` obrigatórios com defaults sensatos.

### HI-013 — Testes da API Dependem de Banco Real
- **Arquivo:** `api/tests/test_api.py`
- **Descrição:** Testes executam contra SQLite no filesystem compartilhado com o agente.
- **Impacto:** Testes não determinísticos; falham se banco em estado inesperado.
- **Recomendação:** Mockar `db.get_conn()` com SQLite `:memory:`.

### HI-014 — Path Traversal Teórico em Screenshots
- **Arquivo:** `frontend/src/pages/Detalhe.tsx:264`
- **Descrição:** `src={`/screenshots/${p.numero}_sistjweb.png`}` sem validação do valor.
- **Impacto:** Se `numero` for comprometido, permite acesso a arquivos fora do diretório.
- **Recomendação:** Validar `p.numero` contra regex CNJ antes de interpolar.

### HI-015 — Mesmo `.env` Compartilhado entre Agente e API
- **Arquivo:** `docker-compose.yml:9,25`
- **Descrição:** Agente precisa de PJE/SISTJ/SMTP; API não deveria ter acesso.
- **Impacto:** Vazamento lateral de credenciais; violação do menor privilégio.
- **Recomendação:** Criar `.env.agente` e `.env.api` separados.

---

## 5. Medium & Low Issues — Resumo por Categoria

### Segurança (🟡/🟢)
| # | Issue | Arquivo | Severidade |
|---|-------|---------|------------|
| M-001 | Input `limit`/`offset` sem bounds | `api/src/rotas/historico.py:19-22` | Médio |
| M-002 | Exception handler genérico amplo | `api/src/app.py:63-69` | Médio |
| M-003 | Log injection em observação de rejeição | `api/src/rotas/aprovacao.py:71` | Médio |
| M-004 | Response models genéricas (`Dict[str, Any]`) | `api/src/rotas/processos.py`, `historico.py` | Médio |
| M-005 | N+1 queries em detalhar processo (4 queries) | `api/src/rotas/processos.py:30-49` | Médio |
| M-006 | JWT sem claims `iss`/`aud` | `api/src/auth.py:41-54` | Baixo |
| M-007 | Sem redirect HTTP→HTTPS | `api/src/app.py` | Baixo |
| M-008 | API sem versionamento no path | `api/src/app.py:29-34` | Baixo |

### Qualidade & Manutenibilidade (🟡/🟢)
| # | Issue | Arquivo | Severidade |
|---|-------|---------|------------|
| M-009 | `processar_processo` com 96 linhas (SRP) | `agente/src/main.py:32-128` | Médio |
| M-010 | Duplicação parser vs extrator_sentenca | `agente/src/modulos/parser.py` + `extrator_sentenca.py` | Médio |
| M-011 | `sys.path.insert` em main.py | `agente/src/main.py:18` | Médio |
| M-012 | `_init_db()` no import global | `agente/src/banco/db.py:174` | Médio |
| M-013 | Side-effects no import de config.py | `agente/src/config.py:11,59-63` | Médio |
| M-014 | Type hint mentiroso (`Optional[int]` vs dict) | `agente/src/banco/db.py:35-42` | Alto |
| M-015 | `datetime.utcnow()` depreciado | `agente/src/utils/logger.py:18` | Baixo |
| M-016 | Imports dentro de métodos de teste | `agente/tests/test_extrator_sentenca.py` | Baixo |
| M-017 | Indicadores de login hardcoded ("SHEILA") | `agente/src/modulos/pje.py:282-283` | Baixo |
| M-018 | REGRAS_OUTROS_ITENS vazias | `agente/src/regras.py:7-28` | Baixo |

### Robustez & Performance (🟡/🟢)
| # | Issue | Arquivo | Severidade |
|---|-------|---------|------------|
| M-019 | Regex com backtracking catastrófico | `agente/src/modulos/extrator_sentenca.py:60-67` | Médio |
| M-020 | Datajud sem retry/backoff | `agente/src/modulos/datajud.py:13-78` | Médio |
| M-021 | `except Exception: pass` no sistjweb | `agente/src/modulos/sistjweb.py:354-356` | Médio |
| M-022 | `except Exception: pass` no pje | `agente/src/modulos/pje.py:404-480` | Médio |
| M-023 | `json.loads` sem log de erro no LLM | `agente/src/modulos/extrator_sentenca.py:261` | Médio |
| M-024 | Slice mágico sem validação | `agente/src/modulos/datajud.py:42` | Baixo |

### Frontend — Qualidade/UX (🟡/🟢)
| # | Issue | Arquivo | Severidade |
|---|-------|---------|------------|
| M-025 | Toast container replicado em 3 páginas | `Fila.tsx`, `Detalhe.tsx`, `Historico.tsx` | Alto |
| M-026 | `useState<any>(null)` | `frontend/src/pages/Detalhe.tsx:14` | Alto |
| M-027 | Interface `Processo` duplicada | `Fila.tsx` + `Historico.tsx` | Médio |
| M-028 | Magic strings de endpoints | Vários | Médio |
| M-029 | Sem React.lazy/Suspense | `frontend/src/App.tsx:5-8` | Médio |
| M-030 | useToast isolado (não global) | `frontend/src/hooks/useToast.ts` | Médio |
| M-031 | Textarea nativa hardcoded | `frontend/src/pages/Detalhe.tsx:298-303` | Médio |
| M-032 | Labels sem htmlFor, botões sem aria-label | `Login.tsx`, `Detalhe.tsx` | Médio |
| M-033 | ThemeToggle inline no App.tsx | `frontend/src/App.tsx:10-33` | Baixo |
| M-034 | Import comentado de Badge | `frontend/src/pages/Detalhe.tsx:6` | Baixo |
| M-035 | Skeleton sem aria-busy | `frontend/src/components/ui/Skeleton.tsx` | Baixo |

### Infra & DevOps (🟡/🟢)
| # | Issue | Arquivo | Severidade |
|---|-------|---------|------------|
| M-036 | Imagem agente gigante (>1.5GB) | `agente/Dockerfile:3-17` | Alto |
| M-037 | `package-lock.json` não copiado | `frontend/Dockerfile:4` | Alto |
| M-038 | `pytest` em requirements de produção | `agente/requirements.txt:4-5` | Alto |
| M-039 | Healthcheck do nginx testa `/health` inexistente | `docker-compose.yml:67` | Alto |
| M-040 | Sem `security_opt`, `read_only`, `cap_drop` | `docker-compose.yml` | Alto |
| M-041 | Sem resource limits | `docker-compose.yml` | Alto |
| M-042 | Crontab com `chmod 0644` | `agente/Dockerfile:21` | Alto |
| M-043 | Credenciais judiciais no mesmo `.env` | `.env.example` | Alto |
| M-044 | Comunicação inter-container em plaintext | `docker-compose.yml` | Alto |
| M-045 | Proxy sem timeout/retry/buffer | `nginx/nginx.conf:11-15` | Alto |
| M-046 | SQLite sem backup/HA | `docker-compose.yml` | Médio |
| M-047 | Agente ausente no docker-compose.dev.yml | `docker-compose.dev.yml` | Médio |
| M-048 | `location /api/` duplicado no frontend nginx | `frontend/nginx-default.conf` | Médio |
| M-049 | Nginx dev na porta 80 (conflito) | `docker-compose.dev.yml:41-42` | Médio |
| M-050 | Sem HEALTHCHECK nos Dockerfiles | `api/Dockerfile`, `frontend/Dockerfile` | Médio |
| M-051 | Cache apt não limpo | `agente/Dockerfile:3-9` | Médio |
| M-052 | package.json sem scripts test/lint | `frontend/package.json` | Baixo |
| M-053 | `.gitignore` genérico | `.gitignore` | Baixo |

---

## 6. Positive Findings

1. **Logging estruturado em JSON** (`agente/src/utils/logger.py`): Logs consistentes e parseáveis, facilitando ingestão em ELK/Loki.
2. **Queries SQLite parametrizadas** (maioria dos endpoints): Uso de `?` placeholders mitiga SQL injection de valores.
3. **Uso de `lifespan` do FastAPI** (`api/src/app.py`): Inicialização controlada moderna, substitui corretamente `@app.on_event`.
4. **Health check ativo de banco** (`api/src/app.py`): Essencial para orquestradores e monitoramento.
5. **Componentes UI com `forwardRef`** (`frontend/src/components/ui/`): Facilitam composição, ref forwarding e testabilidade.
6. **Token refresh com rotação** (`frontend/src/lib/api.ts`): Mitiga replay de tokens comprometidos.
7. **Tema dark/light com `prefers-color-scheme`** (`frontend/src/lib/theme.tsx`): UX moderna e acessível.
8. **Multi-stage build no frontend** (`frontend/Dockerfile`): Reduz tamanho da imagem final.
9. **Hot-reload configurado em dev** (`docker-compose.dev.yml`): Volumes `ro` minimizam riscos de mutação acidental.
10. **Testes unitários para lógica pura do agente**: `test_datajud`, `test_parser`, `test_regras` cobrem edge cases.

---

## 7. Strategic Roadmap

### 7.1 Immediate — Bloqueia Deploy (Próximas 48h)

| # | Tarefa | Responsável | Módulos |
|---|--------|-------------|---------|
| I-01 | Criar `.dockerignore` na raiz | DevOps | Infra |
| I-02 | Remover volume de screenshots do nginx; servir via API autenticada | DevOps + Backend | Infra + API |
| I-03 | Fechar porta 8000 no host (remover do docker-compose) | DevOps | Infra |
| I-04 | Adicionar `JWT_SECRET_KEY` separada; remover fallback hardcoded | Backend | API |
| I-05 | Remover backdoor de autenticação (modo "dev sem senha") | Backend | API |
| I-06 | Corrigir CMD do agente (`cron -f` como PID 1) | DevOps | Infra |
| I-07 | Whitelist de colunas em `salvar_dados_processo` | Backend | Agente + API |
| I-08 | Substituir seletores CSS interpolados por `get_by_text` | Backend | Agente |
| I-09 | Migrar JWT de localStorage para httpOnly cookies | Frontend + Backend | Frontend + API |
| I-10 | Corrigir roteamento aninhado (Outlet) | Frontend | Frontend |
| I-11 | Adicionar `Promise.reject` no catch do refresh | Frontend | Frontend |
| I-12 | Adicionar transação atômica (`BEGIN IMMEDIATE`) na aprovação | Backend | API |
| I-13 | Remover PII de logs (`log_execucao`) | Backend | Agente |
| I-14 | Separar `.env` em `.env.agente` e `.env.api` | DevOps | Infra |

### 7.2 Short-Term — Próximas 2-4 Semanas

| # | Tarefa | Responsável | Módulos |
|---|--------|-------------|---------|
| S-01 | Adicionar rate limiting (`slowapi` ou `fastapi-limiter`) | Backend | API |
| S-02 | Implementar Error Boundaries no frontend | Frontend | Frontend |
| S-03 | Extrair hooks customizados (`useProcesso`, `useAprovar`) | Frontend | Frontend |
| S-04 | Refatorar `Detalhe.tsx` (componentes + hooks) | Frontend | Frontend |
| S-05 | Criar pacote compartilhado (`shared/`) para db.py e schemas | Arquiteto | Agente + API |
| S-06 | Extrair classe base `PlaywrightClient` | Backend | Agente |
| S-07 | Adicionar paginação em `/processos` e `/historico` | Backend | API |
| S-08 | Adicionar security headers no nginx | DevOps | Infra |
| S-09 | Adicionar `USER` não-root em todos os Dockerfiles | DevOps | Infra |
| S-10 | Separar `pytest` para `requirements-dev.txt` | DevOps | Infra |
| S-11 | Adicionar tests no frontend (Vitest + RTL) | Frontend | Frontend |
| S-12 | Implementar refresh token rotation com blacklist | Backend | API |
| S-13 | Adicionar resource limits no compose | DevOps | Infra |
| S-14 | Reduzir tamanho da imagem do agente (multi-stage ou cleanup) | DevOps | Infra |
| S-15 | Sanitizar HTML de email com `html.escape()` | Backend | Agente |

### 7.3 Medium-Term — Próximos 2-3 Meses

| # | Tarefa | Responsável | Módulos |
|---|--------|-------------|---------|
| M-01 | Migrar de SQLite para PostgreSQL | Arquiteto | Agente + API + Infra |
| M-02 | Adotar Pydantic para payloads do orquestrador | Backend | Agente |
| M-03 | Implementar circuit breaker + cache para Datajud | Backend | Agente |
| M-04 | Adicionar TLS interno / mTLS entre containers | DevOps | Infra |
| M-05 | Introduzir CI/CD com scan de vulnerabilidades (Trivy, Snyk) | DevOps | Infra |
| M-06 | Implementar camada de serviço/repositório na API | Arquiteto | API |
| M-07 | Adicionar observabilidade (métricas, tracing) | DevOps + Backend | Todos |
| M-08 | Documentar decisões de arquitetura (ADRs) | Arquiteto | Todos |
| M-09 | Implementar política de retenção de dados (LGPD) | Compliance | Todos |
| M-10 | Avaliação de segurança por pentest externo | Security | Todos |

---

## 8. Compliance & Governance

### LGPD — Lei Geral de Proteção de Dados

| Requisito | Status | Gap |
|-----------|--------|-----|
| Art. 7, VI — Minimização de dados | ❌ Não atendido | PII em logs (`main.py`), screenshots sem controle de acesso |
| Art. 46 — Segurança da informação | ❌ Não atendido | JWT em localStorage, secret hardcoded, sem rate limiting |
| Art. 50 — Relatório de impacto | ⚠️ Pendente | Sistema processa dados pessoais em escala; RIPD recomendado |
| Art. 42 — Nomeação de DPO | ⚠️ Verificar | Confirmar se órgão possui DPO indicado |
| Art. 55 — Registro de operações | ⚠️ Parcial | `log_execucao` existe mas registra dados excessivos |

### OWASP Top 10 2021 — Mapeamento

| OWASP | Status | Onde |
|-------|--------|------|
| A01:2021 – Broken Access Control | ❌ Crítico | Backdoor auth, screenshots sem auth |
| A02:2021 – Cryptographic Failures | ❌ Crítico | JWT secret inadequado, tokens em localStorage |
| A03:2021 – Injection | ❌ Crítico | SQL estrutural, CSS injection |
| A05:2021 – Security Misconfiguration | ❌ Alto | CORS wildcard, porta 8000 exposta, sem headers |
| A07:2021 – Identification and Auth Failures | ❌ Crítico | Backdoor login, refresh sem rotação |
| A09:2021 – Security Logging Failures | ⚠️ Médio | Logs em texto simples, PII em logs |

---

## 9. Appendices

### A. Scorecards Detalhados por Módulo

| Módulo | Score | Bloqueadores | Alto | Médio | Baixo | Parecer |
|--------|-------|-------------|------|-------|-------|---------|
| Agente | 6.5/10 | 2 | 8 | 10 | 5 | REPROVADO |
| API | 4.0/10 | 3 | 9 | 6 | 4 | REPROVADO |
| Frontend | 4.0/10 | 3 | 10 | 6 | 2 | REPROVADO |
| Cross-cutting | 3.5/10 | 7 | 11 | 7 | 5 | REPROVADO |
| **Global** | **4.5/10** | **15** | **38** | **29** | **16** | **REPROVADO** |

### B. Matriz de Responsabilidade

| Papel | Responsabilidades |
|-------|-------------------|
| **DevOps / SRE** | Docker hardening, nginx headers, `.dockerignore`, separação de `.env`, resource limits, TLS interno, CI/CD, PostgreSQL migration |
| **Backend Senior (FastAPI/Python)** | JWT fix, auth backdoor remoção, race condition, rate limiting, refresh rotation, service layer, Pydantic schemas, paginação, tests |
| **Frontend Senior (React/TS)** | httpOnly cookies, Error Boundaries, hooks extraction, component refactoring, tests, a11y fixes, routing fix |
| **Arquiteto de Software** | Pacote compartilhado, PlaywrightClient base, camada de serviço, ADRs, PostgreSQL migration design |
| **Security Officer** | Pentest externo, RIPD, DPO verificação, LGPD compliance, secrets management (Vault) |
| **QA Engineer** | Testes de integração, mocks, cobertura mínima 60%, testes de regressão, testes de carga |

### C. Referências

- **CWE:** MITRE Common Weakness Enumeration (cwe.mitre.org)
- **OWASP Top 10 2021:** owasp.org/Top10/
- **LGPD:** Lei nº 13.709/2018
- **NIST SSDF:** SP 800-218 — Secure Software Development Framework
- **CIS Docker Benchmark:** cisecurity.org/benchmark/docker
- **Playwright Best Practices:** playwright.dev/docs/best-practices
- **FastAPI Security:** fastapi.tiangolo.com/tutorial/security/

---

> *Relatório produzido via code review em 4 waves, cobrindo 61 artefatos de código, infraestrutura e configuração. Recomenda-se reavaliação após correção dos 15 bloqueadores críticos.*
