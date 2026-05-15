# Enterprise Code Review Report

## SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)

**Data:** 2026-05-15
**Classificação:** CONFIDENCIAL
**Versão:** 1.0

---

## 1. Executive Summary

### 1.1 Visão Geral

O SOG (Sistema de Ordem de Guias) é uma plataforma de automação para cálculo e emissão de custas processuais no âmbito do TJDFT. O sistema integra-se aos portais judiciais PJE e SISTJWEB via automação navegacional (Playwright), orquestra aprovações de valores em pipeline e disponibiliza interface web para gestão operacional.

**Stack Tecnológico:**
- **Agente de Automação:** Python 3.12 + Playwright
- **API:** FastAPI + SQLite + JWT
- **Frontend:** React 18 + Vite + Tailwind CSS
- **Infraestrutura:** Docker Compose + Nginx

### 1.2 Metodologia do Review

O review foi conduzido em quatro waves especializadas, cobrindo aproximadamente 45 arquivos-fonte e levantando **98 issues** classificadas por severidade (Critical, High, Medium, Low). Cada wave avaliou um domínio arquitetural distinto, com sobreposição intencional para identificar falhas cross-cutting.

| Wave | Domínio | Issues | Critical | High | Medium | Low | Score |
|------|---------|--------|----------|------|--------|-----|-------|
| 1 | Agente (Python/Playwright) | 25 | 2 | 8 | 10 | 5 | 6.5/10 |
| 2 | API (FastAPI) | 22 | 3 | 9 | 6 | 4 | 4.0/10 |
| 3 | Frontend (React) | 21 | 3 | 10 | 6 | 2 | 4.0/10 |
| 4 | Cross-Cutting (Infra/Security) | 30 | 7 | 11 | 7 | 5 | 3.5/10 |
| **Total** | — | **98** | **15** | **38** | **29** | **16** | **4.5/10** |

> Nota: após deduplicação cross-wave, o consolidado apresenta **13 issues críticos únicos** e **34 issues de alto impacto únicas**, discutidos nas Seções 3 e 4.

### 1.3 Veredicto Global

**Parecer: REPROVADO para produção.**

A base de código apresenta múltiplas vulnerabilidades de segurança que expõem dados de processos judiciais, informações pessoais (CPF/CNPJ) e valores monetários a riscos de vazamento, manipulação e não-repúdio. A infraestrutura Docker carece de hardening básico, e a arquitetura atual (SQLite compartilhado, secrets embarcados, ausência de rate limiting) não suporta operação em ambiente que manipule dados sensíveis de jurisdição.

**Riscos de negócio principais:**
1. **Violação LGPD:** vazamento de screenshots, PII em logs e falta de controles de acesso adequados.
2. **Perda financeira:** race condition em aprovação permite duplo pagamento de custas.
3. **Comprometimento de sessões:** JWT armazenado em `localStorage` + backdoor de autenticação permitem escalada de privilégios.
4. **Corrupção de dados judiciais:** SQLite compartilhado entre agente e API sem controle de concorrência.

---

## 2. Risk Heat Map

| Categoria | Agente | API | Frontend | Infra | Total Critical |
|-----------|--------|-----|----------|-------|----------------|
| **Injeção / Manipulação** | 2 | 1 | 0 | 0 | 3 |
| **Autenticação / Autorização** | 0 | 3 | 2 | 1 | 6 |
| **Exposição de Dados (LGPD)** | 1 | 0 | 1 | 3 | 5 |
| **Concorrência / Integridade** | 0 | 1 | 0 | 2 | 3 |
| **Configuração / Deploy** | 0 | 0 | 0 | 4 | 4 |
| **Qualidade / Manutenibilidade** | 0 | 0 | 0 | 0 | 0 |

> Legenda: células com valor > 0 indicam issues críticos na interseção. O mapeamento orienta alocação de recursos de correção.

---

## 3. Critical Issues (🔴) — Deduplicados e Consolidados

Foram identificadas 15 ocorrências brutas de severidade crítica. Após deduplicação cross-wave (SQL injection em `db.py`, problemas de JWT em `auth.py`, injeção CSS em seletores Playwright), o consolidado apresenta **13 issues críticos únicos**, ordenados por impacto de negócio.

---

### CRIT-01 — Screenshots de Processos Judiciais Expostos Sem Autenticação

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `docker-compose.yml:59` |
| **Módulos** | Infra, Agente, Frontend |
| **Descrição** | Volume `./dados/screenshots:/usr/share/nginx/html/screenshots:ro` expõe capturas de tela de processos judiciais via nginx **sem qualquer controle de autenticação ou autorização**. Qualquer requisição direta ao path consegue acessar documentos sensíveis. |
| **Impacto de Negócio** | **Violação grave da LGPD** (art. 46, 50). Vazamento de dados processuais sigilosos. Risco de responsabilização civil e administrativa do TJDFT. |
| **Recomendação** | Remover volume de screenshots do nginx imediatamente. Servir screenshots apenas via API autenticada (validando JWT + ownership do processo). Migrar storage para bucket S3/minIO com presigned URLs. |
| **Responsável** | DevOps / Security |

---

### CRIT-02 — Race Condition em Aprovação de Custas (Duplo Pagamento)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `api/src/rotas/aprovacao.py:36-55` |
| **Módulos** | API |
| **Descrição** | A rota de aprovação executa `SELECT status` e `UPDATE` em conexões SQLite separadas, **sem transação atômica**. Condição de corrida permite que duas requisições simultâneas aprovem o mesmo processo. |
| **Impacto de Negócio** | **Perda financeira direta:** dupla emissão de guia de custas = duplo pagamento. Inconsistência contábil e judicial irreversível sem compensação manual. |
| **Recomendação** | Envolver SELECT+UPDATE em transação com `BEGIN IMMEDIATE` ou usar `UPDATE ... WHERE status = 'pendente'` como operação atômica. Implementar controle de idempotência via `Idempotency-Key`. |
| **Responsável** | dev_senior (backend) |

---

### CRIT-03 — JWT Secret Fraco com Backdoor de Autenticação

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `api/src/auth.py:19`, `api/src/auth.py:95-101` |
| **Módulos** | API |
| **Descrição** | (a) `SECRET_KEY` é derivado de hash bcrypt (`DASHBOARD_SENHA_HASH`), algoritmo inadequado para HMAC-SHA256, com fallback hardcoded `"dev-secret-change-in-production"`. (b) `authenticate_user` retorna `True` para qualquer senha quando o hash armazenado é inválido ou ausente. |
| **Impacto de Negócio** | **Forjamento de tokens JWT** e bypass total de autenticação. Permite aprovar/rejeitar custas sem credenciais válidas, comprometendo audit trail e não-repúdio. |
| **Recomendação** | Gerar `JWT_SECRET_KEY` via `secrets.token_urlsafe(64)` em deployment. Remover fallback hardcoded. Corrigir lógica de `authenticate_user` para falhar fechadamente em qualquer condição inválida. |
| **Responsável** | Security / dev_senior |

---

### CRIT-04 — SQL Injection Estrutural em Persistência de Processos

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `agente/src/banco/db.py:93-110` |
| **Módulos** | Agente, API |
| **Descrição** | `salvar_dados_processo` concatena nomes de colunas via f-string a partir de `dados.keys()` **sem whitelist**. Atacante pode manipular chaves do dicionário para injetar SQL (ex: `DROP TABLE`, `ALTER TABLE`). |
| **Impacto de Negócio** | Manipulação de schema e integridade de dados judiciais. Possível exfiltração via UNION-based injection. Compromete base de custas processuais. |
| **Recomendação** | Implementar whitelist explícita de colunas permitidas. Rejeitar chaves não mapeadas. Usar queries parametrizadas para valores *e* validação de schema para colunas. |
| **Responsável** | dev_senior |

---

### CRIT-05 — SQLite Compartilhado Entre Agente e API via Volume

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `docker-compose.yml:11,27` |
| **Módulos** | Infra, Agente, API |
| **Descrição** | O mesmo arquivo SQLite é montado via volume em dois containers (agente e API), operando sem mecanismo de locking distribuído ou transações serializadas entre processos. |
| **Impacto de Negócio** | **Corrupção de dados:** race conditions em writes simultâneos podem corromper a base (WAL mode mitiga parcialmente, mas não elimina). Inconsistência no status de processos = guias emitidas incorretamente. |
| **Recomendação** | Imediato: garantir que apenas um processo escreva por vez (file lock ou fila). Curto prazo: migrar para PostgreSQL com pool de conexões. |
| **Responsável** | Arquiteto / DevOps |

---

### CRIT-06 — JWT e Refresh Token Armazenados em localStorage (XSS)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `frontend/src/lib/api.ts:8,21-26,30-31` |
| **Módulos** | Frontend |
| **Descrição** | `access_token` e `refresh_token` são persistidos em `localStorage`. Qualquer vulnerabilidade XSS (script injection via observação maliciosa, dependência comprometida, etc.) permite exfiltração total dos tokens. |
| **Impacto de Negócio** | Comprometimento completo de sessões administrativas. Atacante pode aprovar/rejeitar custas em nome de usuários legítimos. |
| **Recomendação** | Migrar imediatamente para cookies `HttpOnly; Secure; SameSite=Strict`. Implementar rotação de refresh tokens no backend. Adicionar CSRF protection. |
| **Responsável** | dev_senior (frontend + backend) |

---

### CRIT-07 — Injeção em Seletores CSS do Playwright

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `agente/src/modulos/pje.py:120-128`, `agente/src/modulos/sistjweb.py:464` |
| **Módulos** | Agente |
| **Descrição** | `_clicar_por_texto_exato` interpola `texto` cru em f-string `f"text='{texto}'"`. Aspas simples no input quebram o seletor e permitem injeção de pseudo-seletores. O número de processo é usado de forma similar no SISTJWEB. |
| **Impacto de Negócio** | Falha de automação em processos com apóstrofo no nome da parte. Potencial para comportamento imprevisível do navegador automatizado. |
| **Recomendação** | Substituir por `page.get_by_text(texto, exact=True)` da API Playwright, que escapa automaticamente. Implementar sanitização centralizada de seletores. |
| **Responsável** | dev_senior |

---

### CRIT-08 — PII Completa em Logs de Execução

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `agente/src/main.py:52,66` |
| **Módulos** | Agente |
| **Descrição** | Função `log_execucao` registra nome da parte, CPF/CNPJ e valor monetário em texto plano nos logs do sistema. |
| **Impacto de Negócio** | **Violação LGPD** (art. 50, §2º). Logs são copiados para SIEM, backup e análise. PII em texto plano expõe titulares a riscos de identificação e vazamento. |
| **Recomendação** | Remover PII identificável dos logs. Substituir por hashes ou identificadores internos (`processo_id`). Criar classe `SafeLog` com allow-list de campos. |
| **Responsável** | dev_senior |

---

### CRIT-09 — Roteamento Aninhado Incorreto (Comportamento Imprevisível)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `frontend/src/App.tsx:82-96` |
| **Módulos** | Frontend |
| **Descrição** | Componente `<Routes>` está aninhado dentro de outro `<Routes>`. Comportamento não definido pela especificação react-router. Páginas 404 e rotas protegidas falham silenciosamente. |
| **Impacto de Negócio** | Usuários podem acessar páginas que deveriam estar protegidas, ou receber tela em branco em rotas válidas. Impacto operacional em produção. |
| **Recomendação** | Flatten da árvore de rotas. Usar `<Outlet>` para layouts aninhados conforme padrão react-router v6. |
| **Responsável** | dev_senior (frontend) |

---

### CRIT-10 — Refresh Token com Erro Silenciado (Promise Nunca Rejeitada)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `frontend/src/lib/api.ts:29-32` |
| **Módulos** | Frontend |
| **Descrição** | No interceptor de resposta, quando o refresh token falha, o erro é capturado mas a Promise original **nunca é rejeitada**. Requisições pendentes ficam em estado de loading indefinidamente (memory leak). |
| **Impacto de Negócio** | Degradação de UX e consumo de memória do cliente. Em cenário de sessão expirada, usuário fica preso sem feedback. |
| **Recomendação** | Rejeitar Promise original com erro customizado (`SessionExpiredError`) e redirecionar para tela de login. Implementar timeout máximo para requisições. |
| **Responsável** | dev_senior (frontend) |

---

### CRIT-11 — API Exposta em Porta Direta (Bypass do Nginx)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `docker-compose.yml:28` |
| **Módulos** | Infra |
| **Descrição** | Container da API publica porta `8000` no host, permitindo acesso direto sem passar pelo nginx (sem rate limit, sem WAF, sem headers de segurança). |
| **Impacto de Negócio** | Amplificação de ataques (força bruta em `/auth/login` sem proteção de edge). Bypass de todas as políticas de segurança do nginx. |
| **Recomendação** | Remover mapeamento de porta `8000` no `docker-compose.yml` de produção. API deve ser acessível apenas via rede interna Docker (`expose`, não `ports`). |
| **Responsável** | DevOps |

---

### CRIT-12 — Código do Agente Copiado para Imagem da API

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `api/Dockerfile:9` (`COPY agente/src/ ./agente_src/`) |
| **Módulos** | Infra, API, Agente |
| **Descrição** | A imagem Docker da API contém código-fonte completo do agente de automação, incluindo credenciais potenciais e lógica de acesso a sistemas judiciais. |
| **Impacto de Negócio** | Aumento de superfície de ataque. Se a API for comprometida, o atacante obtém acesso ao código de automação judicial e potenciais credenciais embarcadas. |
| **Recomendação** | Criar pacote Python compartilhado (`sog-common`) com apenas os módulos de domínio necessários (models, schemas, db utils). Nunca copiar código do agente para a API. |
| **Responsável** | Arquiteto / DevOps |

---

### CRIT-13 — Container do Agente com Privilégios Excessivos

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `agente/Dockerfile:1-25` |
| **Módulos** | Infra |
| **Descrição** | Container executa como `root`, instala `cron` (processo privilegiado) e usa shell form no `CMD`, causando comportamento inadequado de inicialização. |
| **Impacto de Negócio** | Escalonamento de privilégios em caso de escape de container. `cron` como daemon principal viola princípio de single process por container. |
| **Recomendação** | Criar usuário não-root (`USER sog`). Substituir `cron` por scheduler em processo Python (APScheduler) ou sidecar. Usar exec form no `CMD` (`["python", "-m", "agente"]`). |
| **Responsável** | DevOps |

---

## 4. High Issues (🟠) — Top 15 por Impacto

Após deduplicação, foram identificadas 34 issues de severidade **High** únicas. As 15 mais impactantes para o negócio estão listadas abaixo.

| ID | Issue | Arquivo | Impacto | Recomendação | Resp. |
|----|-------|---------|---------|--------------|-------|
| HIGH-01 | CORS `allow_origins=["*"]` + `allow_credentials=True` | `api/src/app.py:37-43` | Permite requisições credenciadas de qualquer origem. Risco de CSRF e vazamento de tokens. | Restringir `allow_origins` ao domínio do frontend. Remover `allow_credentials` se CORS aberto for necessário. | dev_senior |
| HIGH-02 | Refresh token sem rotação nem blacklist | `api/src/rotas/auth.py:39-55` | Token roubado pode ser usado indefinidamente. | Implementar rotação (novo refresh token a cada uso) e blacklist em storage seguro. | dev_senior |
| HIGH-03 | Ausência total de rate limiting | `api/src/app.py` + rotas | API vulnerável a brute-force e scraping. | Adicionar `slowapi` ou middleware customizado com limites por IP e por usuário. | dev_senior |
| HIGH-04 | `/processos` sem paginação (retorna tudo) | `api/src/rotas/processos.py:18-27` | OOM em bases grandes. Negação de serviço acidental. | Implementar `limit`/`offset` com bounds máximos (ex: `limit <= 100`). | dev_senior |
| HIGH-05 | `threading.Thread` daemon sem controle em aprovação | `api/src/rotas/aprovacao.py:22-33` | Threads não gerenciadas podem vazar ou duplicar execução. | Substituir por executor com pool limitado, timeout e retry controlado. | dev_senior |
| HIGH-06 | Testes de API dependem de banco real compartilhado | `api/tests/test_api.py` | Testes não determinísticos. Falhas flaky mascaram regressões. | Usar banco SQLite em memória (`:memory:`) por teste, com fixture isolada. | dev_senior |
| HIGH-07 | Dados de processos em HTML de email sem sanitização | `agente/src/utils/notificador.py:25-27` | XSS via email se dados do processo contiverem HTML malicioso. | Usar `html.escape()` em todos os valores dinâmicos antes de interpolação. | dev_senior |
| HIGH-08 | Type hint incorreto (`processo_existe` retorna dict, anotado `Optional[int]`) | `agente/src/banco/db.py:35-42` | Erros de runtime mascarados por falsas garantias de tipo. | Corrigir anotação para `Optional[Dict[str, Any]]` ou dataclass. | dev_senior |
| HIGH-09 | Instanciação de clientes a cada emissão (~300MB RAM) | `agente/src/modulos/emissor.py:28-29` | Memory bloat e gargalo de performance em lotes. | Reutilizar client HTTP via connection pooling (`requests.Session`). | dev_senior |
| HIGH-10 | Duplicação idêntica de inicialização Playwright (~70% do código) | `agente/src/modulos/pje.py` + `sistjweb.py` | Manutenção custosa. Correções precisam ser aplicadas em N arquivos. | Extrair classe base `PlaywrightClient` com métodos comuns (login, logout, screenshot). | Arquiteto |
| HIGH-11 | `@retry_on_exception` captura `Exception` genérica | `agente/src/modulos/retry.py:150-213` | Bugs de programação (`NameError`, `TypeError`) são mascarados como falhas transitórias. | Capturar apenas exceções esperadas (`TimeoutError`, `ConnectionError`). | dev_senior |
| HIGH-12 | Ausência total de Error Boundaries no React | `frontend/src/` (global) | Qualquer erro não tratado = tela branca. Perda total de contexto do usuário. | Implementar `<ErrorBoundary>` no nível do layout e nas rotas principais. | dev_senior (frontend) |
| HIGH-13 | `Detalhe.tsx` com 328 linhas (múltiplas responsabilidades) | `frontend/src/pages/Detalhe.tsx` | Impossível testar unitariamente. Regressões frequentes. | Extrair data hooks (`useProcesso`), componentes de UI e lógica de negócio em arquivos separados. | dev_senior (frontend) |
| HIGH-14 | Path de screenshot com interpolação direta (path traversal teórico) | `frontend/src/lib/api.ts` (screenshot path) | Se o número de processo não for validado, `../../etc/passwd` pode ser injetado. | Validar e sanitizar `numero_processo` com regex antes de interpolação em path. | dev_senior (frontend) |
| HIGH-15 | Nginx sem headers de segurança (X-Frame-Options, CSP, HSTS) | `nginx/nginx.conf` + `nginx-dev.conf` | Clickjacking, MIME-sniffing, downgrade attacks. | Adicionar `X-Frame-Options: DENY`, `Content-Security-Policy`, `Strict-Transport-Security`. | DevOps |

---

## 5. Medium & Low Issues — Resumo por Categoria

### 5.1 Segurança

| ID | Issue | Arquivo | Risco |
|----|-------|---------|-------|
| MED-SEC-01 | `requests.post` sem retry/backoff no Datajud | `agente/src/modulos/datajud.py` | Falha transitória = perda de dados. |
| MED-SEC-02 | `except Exception: pass` em pje.py e sistjweb.py | Múltiplos | Erros silenciados dificultam detecção de intrusão. |
| MED-SEC-03 | `json.loads` sem log de erro no extrator_sentenca | `agente/src/modulos/extrator_sentenca.py` | Falha de parsing não audita. |
| MED-SEC-04 | Log injection em observação de rejeição | `api/src/rotas/aprovacao.py` | Quebra de linha em logs pode spoofar entradas. |
| MED-SEC-05 | API sem versionamento no path | `api/src/app.py` | Breaking changes não gerenciáveis. |
| LOW-SEC-01 | JWT sem `iss`/`aud` | `api/src/auth.py` | Tokens não verificam emissor/audiência. |
| LOW-SEC-02 | Sem redirect HTTP→HTTPS | `nginx/` | Downgrade de conexão possível. |

### 5.2 Qualidade e Arquitetura

| ID | Issue | Arquivo | Risco |
|----|-------|---------|-------|
| MED-ARC-01 | `processar_processo` com 96 linhas (viola SRP) | `agente/src/main.py` | Impossível testar. Múltiplas razões para mudar. |
| MED-ARC-02 | Duplicação parser/extrator_sentenca | `agente/src/modulos/` | Lógica de parsing espalhada. |
| MED-ARC-03 | `_init_db()` no import global (side-effect) | `agente/src/banco/db.py` | Import causa execução de código. Dificulta testes. |
| MED-ARC-04 | Side-effects no import de config.py | `agente/src/config.py` | Configuração não é pura. |
| MED-ARC-05 | Slice mágico sem validação em datajud.py | `agente/src/modulos/datajud.py` | IndexError em dados inesperados. |
| MED-ARC-06 | `sys.path.insert` em `main.py` | `agente/src/main.py` | Fragilidade de import. |
| MED-ARC-07 | Response models genéricas `Dict[str, Any]` | `api/src/rotas/*.py` | Perda de validação automática do FastAPI. |
| MED-ARC-08 | Exception handler genérico amplo | `api/src/app.py` | Erros inesperados mascarados. |
| MED-ARC-09 | Interface `Processo` duplicada em 2 arquivos | `frontend/src/` | Divergência de tipos. |
| MED-ARC-10 | Magic strings de endpoints | `frontend/src/lib/api.ts` | Refatoração arriscada. |
| LOW-ARC-01 | Indicadores de login hardcoded ("SHEILA") | `agente/src/modulos/` | Quebra se usuário mudar. |
| LOW-ARC-02 | `REGRAS_OUTROS_ITENS` vazias | `agente/src/modulos/` | Configuração morta. |

### 5.3 Performance

| ID | Issue | Arquivo | Risco |
|----|-------|---------|-------|
| MED-PERF-01 | Regex backtracking em extrator_sentenca | `agente/src/modulos/extrator_sentenca.py` | ReDoS possível em inputs longos. |
| MED-PERF-02 | N+1 queries em detalhar processo (4 queries) | `api/src/rotas/processos.py` | Latência linear com número de processos. |
| MED-PERF-03 | `limit`/`offset` sem bounds | `api/src/rotas/processos.py` | Requisição maliciosa consome recursos. |
| MED-PERF-04 | Sem React.lazy/Suspense | `frontend/src/App.tsx` | Bundle inicial grande. |
| LOW-PERF-01 | `datetime.utcnow()` depreciado | Múltiplos | Warning em Python 3.12+. |
| LOW-PERF-02 | Slice sem validação de comprimento | `agente/src/modulos/` | IndexError silencioso. |

### 5.4 DevOps e Infraestrutura

| ID | Issue | Arquivo | Risco |
|----|-------|---------|-------|
| MED-DEV-01 | Ausência de `security_opt`, `read_only`, `cap_drop` | `docker-compose.yml` | Superfície de ataque ampla. |
| MED-DEV-02 | Sem `deploy.resources.limits` (CPU/memória) | `docker-compose.yml` | Contention e OOM não controlados. |
| MED-DEV-03 | Healthcheck do nginx testa `/health` inexistente | `docker-compose.yml:67` | Healthcheck sempre falha. |
| MED-DEV-04 | Mesmo `.env` compartilhado entre agente e API | `docker-compose.yml` | Princípio do menor privilégio violado. |
| MED-DEV-05 | Imagem do agente >1.5GB sem limpeza | `agente/Dockerfile` | Deploy lento. Armazenamento excessivo. |
| MED-DEV-06 | `frontend/Dockerfile` copia `package.json` sem `package-lock.json` | `frontend/Dockerfile:4` | Build não reproduzível. |
| MED-DEV-07 | `pytest` em requirements de produção | `agente/requirements.txt` | Aumento desnecessário de superfície. |
| MED-DEV-08 | Credenciais judiciais no mesmo `.env` | `.env` | Vazamento de um segredo expõe todos. |
| MED-DEV-09 | Comunicação inter-container em plaintext | `docker-compose.yml` | Sniffing de tráfego interno. |
| MED-DEV-10 | Proxy nginx sem timeout/retry/buffer | `nginx/nginx.conf:11-15` | Conexões zumbis. Latência não controlada. |
| MED-DEV-11 | Ausência total de `.dockerignore` | Raiz do projeto | `.env`, `.git/`, `dados/` podem vazar para layers. |
| LOW-DEV-01 | SQLite sem backup/HA | `docker-compose.yml` | Perda total em falha de disco. |
| LOW-DEV-02 | Agente ausente no `docker-compose.dev.yml` | `docker-compose.dev.yml` | Ambiente de desenvolvimento incompleto. |
| LOW-DEV-03 | `location /api/` duplicado no nginx frontend | `nginx/` | Configuração confusa. |
| LOW-DEV-04 | Nginx dev na porta 80 (conflito com prod) | `docker-compose.dev.yml` | Não pode rodar simultaneamente. |
| LOW-DEV-05 | Sem `HEALTHCHECK` nos Dockerfiles | Múltiplos | Orquestrador não detecta falhas. |
| LOW-DEV-06 | Cache apt não limpo | `agente/Dockerfile` | Imagem inchada. |

### 5.5 Frontend / UX

| ID | Issue | Arquivo | Risco |
|----|-------|---------|-------|
| MED-FE-01 | Toast container replicado em 3 páginas | `frontend/src/pages/` | Manutenção triplicada. |
| MED-FE-02 | `useState<any>(null)` em Detalhe.tsx | `frontend/src/pages/Detalhe.tsx` | Tipagem perdida. Erros em runtime. |
| MED-FE-03 | `useToast` isolado por componente | `frontend/src/` | Estado de notificação disperso. |
| MED-FE-04 | Textarea nativa hardcoded | `frontend/src/pages/` | Sem reutilização. |
| MED-FE-05 | Labels sem `htmlFor`, botões sem `aria-label` | `frontend/src/` | Acessibilidade comprometida. |
| LOW-FE-01 | ThemeToggle inline no App.tsx | `frontend/src/App.tsx` | Componente não testável. |
| LOW-FE-02 | Import comentado de Badge | `frontend/src/` | Código morto. |

---

## 6. Positive Findings

Apesar dos riscos identificados, o projeto apresenta fundamentos sólidos que devem ser preservados e expandidos:

- **Logging JSON estruturado:** o agente utiliza formato estruturado para logs, facilitando ingestão em SIEM e análise automatizada.
- **Testes unitários para lógica pura:** existem testes cobrindo regras de negócio isoladas, demonstrando preocupação com qualidade em parte do código.
- **Resiliência em seletores com fallback:** o agente implementa estratégias alternativas de localização de elementos, reduzindo fragilidade a mudanças de layout nos portais judiciais.
- **Lifespan do FastAPI:** a API utiliza `lifespan` para gerenciamento de recursos (conexões, caches), padrão moderno e recomendado.
- **Health check ativo de banco:** a API verifica conectividade com SQLite no startup, evitando deploys quebrados.
- **HTTPBearer(auto_error=False):** implementação correta de auth scheme que permite controle granular de respostas 401.
- **Token refresh com rotação (parcial):** o frontend implementa mecanismo de refresh automático, base para evolução para rotação completa no backend.
- **Tema dark/light com `prefers-color-scheme`:** respeita preferência do sistema operacional do usuário.
- **Componentes UI com `forwardRef`/`props`:** arquitetura de componentes reutilizáveis já iniciada.
- **Multi-stage build no frontend:** Dockerfile de produção já utiliza multi-stage, reduzindo imagem final.
- **Hot-reload em desenvolvimento:** Vite configurado para desenvolvimento ágil.
- **Variáveis de ambiente centralizadas:** existe preocupação com configuração via env (embora precise de segregação).

---

## 7. Strategic Roadmap

### 7.1 Immediate (bloqueia deploy — próximas 48h)

| # | Ação | Issue(s) | Responsável |
|---|------|----------|-------------|
| 1 | Isolar screenshots do nginx; servir apenas via API autenticada | CRIT-01 | DevOps |
| 2 | Reminar mapeamento de porta 8000 no host; API apenas via nginx | CRIT-11 | DevOps |
| 3 | Corrigir JWT secret (gerar via `secrets.token_urlsafe`) e remover backdoor | CRIT-03 | Security / dev_senior |
| 4 | Corrigir SQL injection em `db.py` com whitelist de colunas | CRIT-04 | dev_senior |
| 5 | Tornar aprovação atômica (transação ou UPDATE condicional) | CRIT-02 | dev_senior |
| 6 | Separar `.env` do agente e da API; nunca compartilhar credenciais | CRIT-05, MED-DEV-08 | DevOps |
| 7 | Corrigir roteamento aninhado do React Router | CRIT-09 | dev_senior (frontend) |
| 8 | Rejeitar Promise no catch do refresh token | CRIT-10 | dev_senior (frontend) |
| 9 | Criar `.dockerignore` (`.env`, `dados/`, `.git/`) | MED-DEV-11 | DevOps |
| 10 | Sanitizar seletores Playwright (`get_by_text` com escape) | CRIT-07 | dev_senior |
| 11 | Remover PII de logs; usar identificadores internos | CRIT-08 | dev_senior |
| 12 | Restringir CORS a origens específicas | HIGH-01 | dev_senior |

### 7.2 Short-term (próximas 2-4 semanas)

| # | Ação | Issue(s) | Responsável |
|---|------|----------|-------------|
| 1 | Migrar tokens para cookies `HttpOnly; Secure; SameSite=Strict` | CRIT-06 | dev_senior (fullstack) |
| 2 | Implementar rate limiting na API (`slowapi`) | HIGH-03 | dev_senior |
| 3 | Adicionar paginação com bounds em `/processos` | HIGH-04 | dev_senior |
| 4 | Refatorar `Detalhe.tsx` em hooks + componentes (< 150 linhas) | HIGH-13 | dev_senior (frontend) |
| 5 | Implementar Error Boundaries no React | HIGH-12 | dev_senior (frontend) |
| 6 | Adicionar headers de segurança no nginx (CSP, HSTS, X-Frame-Options) | HIGH-15 | DevOps |
| 7 | Criar usuário não-root em todos os Dockerfiles | CRIT-13, MED-DEV-02 | DevOps |
| 8 | Adicionar `deploy.resources.limits` no compose | MED-DEV-02 | DevOps |
| 9 | Extrair classe base `PlaywrightClient` | HIGH-10 | Arquiteto |
| 10 | Reutilizar `requests.Session` no emissor | HIGH-09 | dev_senior |
| 11 | Corrigir type hints e adicionar `mypy` em CI | HIGH-08 | dev_senior |
| 12 | Sanitizar HTML de email (`html.escape`) | HIGH-07 | dev_senior |
| 13 | Substituir `threading.Thread` por executor gerenciado | HIGH-05 | dev_senior |
| 14 | Isolar testes de API com banco `:memory:` | HIGH-06 | dev_senior |
| 15 | Corrigir `@retry_on_exception` para capturar apenas exceções esperadas | HIGH-11 | dev_senior |

### 7.3 Medium-term (próximos 2-3 meses)

| # | Ação | Issue(s) | Responsável |
|---|------|----------|-------------|
| 1 | Migrar de SQLite para PostgreSQL (ou outro RDBMS com concorrência real) | CRIT-05 | Arquiteto |
| 2 | Implementar TLS interno / mTLS entre containers | MED-DEV-09 | DevOps |
| 3 | Adotar Pydantic para validação de payloads e response models | MED-ARC-07 | Arquiteto |
| 4 | Criar camada de serviço/repositório (separação de concerns) | MED-ARC-01 | Arquiteto |
| 5 | Implementar CI/CD com Trivy (scan de imagens), Snyk (dependências), Hadolint (Dockerfile) | Múltiplos | DevOps |
| 6 | Adicionar testes no frontend (Vitest + React Testing Library) | Zero testes | dev_senior (frontend) |
| 7 | Implementar circuit breaker e rate limiting para Datajud | MED-SEC-01 | dev_senior |
| 8 | Criar pacote compartilhado `sog-common` para models/utils | CRIT-12, HIGH-10 | Arquiteto |
| 9 | Adicionar audit trail completo (quem aprovou, quando, de qual IP) | Compliance | Security |
| 10 | Implementar backup automatizado de banco de dados | LOW-DEV-01 | DevOps |

---

## 8. Compliance & Governance

### 8.1 LGPD (Lei 13.709/2018)

O sistema processa dados pessoais sensíveis (CPF/CNPJ, nomes de partes em processos judiciais) e dados de natureza financeira (valores de custas). As seguintes obrigações estão **não atendidas** no estado atual:

| Princípio / Obrigação | Status | Issue Relacionada |
|-----------------------|--------|-------------------|
| Segurança (art. 46) | **NÃO ATENDIDO** | CRIT-01, CRIT-03, CRIT-06, CRIT-08, HIGH-15 |
| Mínimo necessário de dados | **PARCIAL** | CRIT-08 (PII em logs) |
| Registro de operações (art. 50) | **PARCIAL** | CRIT-03 (backdoor quebra audit trail) |
| Correção e atualização | **ATENDIDO** (parcialmente) | — |

**Recomendação:** conduzir avaliação formal de impacto à proteção de dados (AIPD/RIPD) antes de colocar o sistema em produção com dados reais.

### 8.2 Segurança da Informação

O projeto não atende aos controles básicos da OWASP Top 10 2021:

- **A01:2021-Broken Access Control** — CRIT-01, CRIT-03, CRIT-06, CRIT-11
- **A03:2021-Injection** — CRIT-04, CRIT-07
- **A05:2021-Security Misconfiguration** — CRIT-13, MED-DEV-01, MED-DEV-04
- **A07:2021-Identification and Authentication Failures** — CRIT-03, HIGH-02
- **A08:2021-Software and Data Integrity Failures** — CRIT-05 (corrupção de dados)

### 8.3 Audit Trail

A aprovação de custas deve ser **irreversível e auditável**. Requisitos pendentes:
- Hash de token de quem aprovou
- Timestamp com timezone (UTC)
- IP de origem
- Hash do payload aprovado (para detectar tampering)
- Retenção mínima de 5 anos (conforme normas do CNJ)

---

## 9. Appendices

### A. Scorecards Detalhados por Módulo

#### Wave 1 — Agente de Automação (Python/Playwright)

| Dimensão | Nota | Justificativa |
|----------|------|---------------|
| Segurança | 4/10 | SQL injection, injeção CSS, PII em logs |
| Qualidade | 6/10 | Type hints incorretos, SRP violado, duplicação |
| Performance | 6/10 | Instanciação excessiva de clients, duplicação de inicialização Playwright |
| Testabilidade | 7/10 | Testes unitários existentes para lógica pura |
| Manutenibilidade | 5/10 | Código duplicado, magic strings, imports side-effect |
| **Score Geral** | **6.5/10** | — |

#### Wave 2 — API (FastAPI)

| Dimensão | Nota | Justificativa |
|----------|------|---------------|
| Segurança | 3/10 | JWT fraco, backdoor auth, CORS aberto, sem rate limit |
| Qualidade | 5/10 | Response models genéricas, exception handler amplo |
| Performance | 5/10 | Sem paginação, N+1 queries, threads sem controle |
| Testabilidade | 3/10 | Testes com banco real compartilhado (não determinísticos) |
| Manutenibilidade | 4/10 | `sys.path.insert` para importar agente, sem camada de serviço |
| **Score Geral** | **4.0/10** | — |

#### Wave 3 — Frontend (React)

| Dimensão | Nota | Justificativa |
|----------|------|---------------|
| Segurança | 3/10 | localStorage JWT, sem CSP, path traversal teórico |
| Qualidade | 4/10 | `any` types, componentes monolíticos, magic strings |
| Performance | 5/10 | Sem lazy loading, bundle não otimizado |
| Testabilidade | 1/10 | Zero testes |
| UX/Acessibilidade | 4/10 | Sem Error Boundaries, labels sem htmlFor, sem aria-label |
| **Score Geral** | **4.0/10** | — |

#### Wave 4 — Cross-Cutting (Infra/Security)

| Dimensão | Nota | Justificativa |
|----------|------|---------------|
| Segurança | 2/10 | Root containers, sem hardening, screenshots expostos, sem headers |
| Confiabilidade | 3/10 | SQLite compartilhado, healthcheck quebrado, CMD shell form |
| Reprodutibilidade | 4/10 | Sem package-lock, sem .dockerignore, pytest em prod |
| Governança | 4/10 | Sem segregação de envs, credenciais concentradas |
| Observabilidade | 5/10 | Logs de texto plano, healthcheck mal configurado |
| **Score Geral** | **3.5/10** | — |

### B. Matriz de Responsabilidade

| Perfil | Responsabilidades Principais |
|--------|------------------------------|
| **Arquiteto** | Separação de módulos (sog-common), migração para PostgreSQL, camada de serviço/repositório, async database driver, definição de contratos de API |
| **dev_senior (Backend)** | Correção de SQL injection, atomicidade de aprovação, JWT seguro, rate limiting, paginação, refatoração de retry/exception handling, testes determinísticos |
| **dev_senior (Frontend)** | Migração para httpOnly cookies, Error Boundaries, refatoração de Detalhe.tsx, tipagem correta, testes de componentes, sanitização de paths |
| **DevOps / SRE** | Hardening de containers (USER não-root, cap_drop, read_only), nginx headers de segurança, fechamento de porta 8000, .dockerignore, resource limits, TLS interno, CI/CD com scanners |
| **Security / Compliance** | LGPD audit trail, AIPD/RIPD, validação de headers CSP, revisão de armazenamento de credenciais, rotação de secrets |

### C. Referências

- **OWASP Top 10:2021** — https://owasp.org/Top10/
- **OWASP ASVS 4.0** — https://github.com/OWASP/ASVS
- **CWE/SANS Top 25** — https://cwe.mitre.org/top25/
- **LGPD — Lei nº 13.709/2018** — https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- **CNJ Resolução nº 331/2020** — Política Nacional de Segurança da Informação do Poder Judiciário
- **FastAPI Security Best Practices** — https://fastapi.tiangolo.com/tutorial/security/
- **Docker Security Cheat Sheet** — https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- **Playwright Best Practices** — https://playwright.dev/docs/best-practices
- **React Router v6** — https://reactrouter.com/en/main/start/overview

---

*Documento elaborado em 2026-05-15. Distribuição restrita à equipe técnica e stakeholders autorizados do projeto SOG.*
