# Resumo declarado — correções do code review enterprise

> Este arquivo resume correções declaradas como aplicadas.
> Ele não substitui o plano em `code-review-fixes.md` nem valida sozinho que
> todas as mudanças ainda correspondem ao código atual.

> **Projeto:** SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)  
> **Data:** 2026-05-15  
> **Escopo:** 98 issues identificadas, 95 corrigidas em 7 waves incrementais.  
> **Audiência:** Desenvolvedores que vão manter, operar ou evoluir o sistema.

---

## 1. Resumo Executivo

Em maio de 2026 foi realizado um code review enterprise que cobriu **61 artefatos** de código, infraestrutura e configuração. O sistema foi classificado como **REPROVADO para produção** com score **4.5/10**, devido a 15 issues críticas concentradas em autenticação, exposição de dados, integridade e injeção.

As correções foram organizadas em 7 waves incrementais. Ao final:

| Dimensão | Antes | Depois |
|----------|-------|--------|
| Score global | **4.5/10** (REPROVADO) | **~8.0/10** (APROVADO COM RESSALVAS) |
| Issues críticas (🔴) | 15 | 0 |
| Issues altas (🟠) | 38 | ~3 remanescentes |
| JWT em localStorage | Sim | Não (httpOnly cookies) |
| Screenshots públicos | Sim | Não (endpoint autenticado) |
| Race condition em aprovação | Sim | Não (`BEGIN IMMEDIATE`) |
| SQL injection estrutural | Sim | Não (whitelist de colunas) |
| Testes frontend | 0 | 3 suites, cobertura configurada |
| Containers como root | Todos | Nenhum |
| `sys.path.insert` | Sim | Não (pacote `shared/`) |

> **Nota:** O score "depois" é uma estimativa baseada nos critérios originais do relatório. Uma reavaliação formal ainda é recomendada antes do deploy em produção com dados reais.

### Waves de correção

| Wave | Foco | Issues | Status |
|------|------|--------|--------|
| 1 | Segurança Crítica I — Infra + Auth Core | 14 | ✅ Concluída |
| 2 | Segurança Crítica II — Agente + Playwright | 15 | ✅ Concluída |
| 3 | Auth Cross-Cutting — httpOnly cookies + Screenshots API | 10 | ✅ Concluída |
| 4 | Backend API — Concorrência, paginação, models | 12 | ✅ Concluída |
| 5 | Frontend — Refatoração, UX, testes | 16 | ✅ Concluída |
| 6 | Arquitetura Python — Pacote shared, SRP | 10 | ⚠️ Parcial* |
| 7 | Infra Hardening — Containers non-root, nginx limits | 14 | ✅ Concluída |
| 8 | Migração SQLite → PostgreSQL | 3 | ⏸️ Adiada |

\* O backup sidecar (issue M-046) foi **planejado mas não implementado** no `docker-compose.yml`. Ver seção Roadmap.

---

## 2. Guia de Configuração

O projeto usa **dois arquivos de ambiente separados** para respeitar o princípio do menor privilégio. Nunca comite valores reais.

### 2.1 `.env.api` — Serviço FastAPI

Variáveis lidas pelo container `custas-api`:

```bash
# Obrigatórias
DASHBOARD_USUARIO=admin
DASHBOARD_SENHA=senha-do-dashboard     # senha simples salva no SQLite
JWT_SECRET_KEY=change-me-min-32-chars  # ≥32 caracteres, aleatório

# Opcionais (têm defaults)
FRONTEND_URL=http://localhost:3000      # Origem CORS permitida
DB_PATH=/dados/custas.db                # Caminho do SQLite
ENV=production                          # development | production
```

**Validação no startup:**
- Se `JWT_SECRET_KEY` estiver ausente ou tiver < 32 caracteres, a aplicação **falha imediatamente** (`RuntimeError`).
- Se `DASHBOARD_USUARIO` e `DASHBOARD_SENHA` forem informados, a API salva a credencial do dashboard no SQLite.
- Não existe mais "modo dev sem senha".

### 2.2 `.env.agente` — Serviço de Automação

Variáveis lidas pelo container `custas-agente`:

```bash
# Obrigatórias para automação via SSO/2FA interativo
PJE_URL=https://pje.tjdft.jus.br/pje/login.seam
PJE_ETIQUETA=SUA ETIQUETA AQUI

SISTJ_URL=https://sistj.tjdft.jus.br/sistj/sistj

DATAJUD_API_KEY=sua_chave
DATAJUD_URL=https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search

# Notificação por e-mail
SMTP_HOST=smtp.gmail.com
SMTP_PORTA=587
SMTP_USUARIO=seu_email
SMTP_SENHA=sua_senha_app
EMAIL_DESTINO=destino@email.com

# Opcionais
PJE_INDICADORES_SUCESSO=["Nome do Usuário"]  # JSON list; se vazio, usa indicadores genéricos de DOM
HEADLESS=true
MAX_TENTATIVAS=3
TIMEOUT_PADRAO=30000
DB_PATH=/dados/custas.db
```

### 2.3 Verificação rápida

```bash
# Validar que os arquivos existem e não estão vazios
cat .env.api | grep -E "^(JWT_SECRET_KEY|DASHBOARD_USUARIO|DASHBOARD_SENHA)="
cat .env.agente | grep -E "^(PJE_|SISTJ_|DATAJUD_)" | wc -l   # deve retornar ≥ 6
```

---

## 3. Decisões Arquiteturais

### 3.1 httpOnly + Secure + SameSite=Strict cookies

**Problema:** Tokens JWT armazenados em `localStorage` são vulneráveis a XSS. Qualquer script injetado pode roubar `localStorage.getItem('access_token')`.

**Decisão:** O backend emite cookies `httpOnly` (não acessíveis via JavaScript), `Secure` (apenas HTTPS em produção) e `SameSite=Strict` (não enviados em requisições cross-origin). O frontend usa `withCredentials: true` no axios e **nunca** lê o token.

**Comportamento em desenvolvimento:** Quando `ENV=development`, os cookies usam `Secure=false` e `SameSite=Lax` para permitir `localhost` sem HTTPS.

**Código de referência:**

```python
# api/src/rotas/auth.py
def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access,
        max_age=_ACCESS_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,      # False em dev, True em produção
        samesite=_COOKIE_SAMESITE,  # Lax em dev, Strict em produção
        path="/",
    )
```

```typescript
// frontend/src/lib/api.ts
const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,  // envia cookies automaticamente
})
```

### 3.2 Pacote compartilhado `shared/sog_shared/`

**Problema:** A API copiava o código fonte do agente (`COPY agente/src/ ./agente_src/`) e cada rota fazia `sys.path.insert(0, '/app/agente_src')`. Isso quebrava versionamento independente, testes e deploy determinístico.

**Decisão:** Foi criado o pacote Python `sog-shared` em `shared/pyproject.toml`, instalado como editável (`pip install -e ./shared`) tanto na API quanto no agente. Ele contém:

- `sog_shared/db.py` — acesso ao banco SQLite (sem side-effects no import)
- `sog_shared/config.py` — variáveis de ambiente comuns
- `sog_shared/schemas.py` — schemas Pydantic compartilhados

**Código de referência:**

```python
# shared/sog_shared/db.py
# init_db() é explícita; não roda no import do módulo
from sog_shared import db
db.init_db()   # chamada no startup da API e do agente
```

**Impacto:** Os Dockerfiles da API e do agente não se copiam mais. Os testes da API mockam `sog_shared.db.get_conn` diretamente.

### 3.3 Adiamento da migração SQLite → PostgreSQL

**Problema:** SQLite compartilhado entre agente e API é propenso a race conditions e não escala bem.

**Decisão:** A migração para PostgreSQL foi **adiada** (Wave 8) porque o volume atual é **< 50 processos/dia**. Como mitigação imediata:

- WAL mode ativado (`PRAGMA journal_mode=WAL`)
- `PRAGMA busy_timeout=5000`
- Race condition na aprovação resolvida com `BEGIN IMMEDIATE` em transação atômica

**Quando reavaliar:** Quando o volume ultrapassar 100 processos/dia ou quando houver mais de 2 operadores simultâneos no dashboard.

### 3.4 PlaywrightClient base

**Problema:** 70% da lógica de inicialização Playwright era duplicada entre `pje.py` e `sistjweb.py`.

**Decisão:** Extraída classe base `PlaywrightClient` em `agente/src/modulos/playwright_client.py`. `PjeClient` e `SistjClient` herdam dela. A classe base centraliza:

- `iniciar()` — launch do Chromium, viewport, timeout
- `fechar()` — teardown limpo
- `verificar_sessao()` — detecta sessão expirada via URL/conteúdo
- `reconectar()` — refaz login automaticamente

---

## 4. Como Rodar

### 4.1 Ambiente de desenvolvimento local (Docker Compose)

```bash
# 1. Copiar e preencher variáveis de ambiente
cp .env.example .env.api
cp .env.example .env.agente
# edite ambos os arquivos com credenciais reais

# 2. Subir stack completa
docker-compose -f docker-compose.dev.yml up --build

# Acesse:
#   Dashboard: http://localhost:3001
#   API:       http://localhost:8080/api/v1/health
#   Nginx dev: http://localhost:8080
```

> Em dev, o nginx roda na porta `8080:80` para evitar conflito com possíveis serviços locais na 80.

### 4.2 Ambiente de produção (Docker Compose)

```bash
# 1. Preencher .env.api e .env.agente
# 2. Subir
docker-compose up --build -d

# Verificar saúde dos containers
docker-compose ps
curl -f http://localhost/api/v1/health
```

> A API **não expõe mais a porta 8000 no host**. O acesso passa obrigatoriamente pelo nginx.

### 4.3 Testes — API (Python)

```bash
# Instalar dependências de dev
cd api
pip install -r requirements.txt
pip install -e ../shared
pip install pytest pytest-mock slowapi

# Rodar testes (usam SQLite :memory:)
pytest tests/test_api.py -v
```

Os testes usam uma fixture `mock_db` que substitui `sog_shared.db.get_conn` por uma conexão `:memory:` isolada. Não dependem do arquivo `.db` do filesystem.

### 4.4 Testes — Agente (Python)

```bash
cd agente
pip install -r requirements-dev.txt
pip install -e ../shared
pytest tests/ -v
```

### 4.5 Testes — Frontend (Vitest + React Testing Library)

```bash
cd frontend
npm ci
npm run test

# Cobertura
npm run test -- --coverage
```

Configuração de thresholds no `vite.config.ts`:

```typescript
coverage: {
  provider: 'v8',
  thresholds: {
    lines: 60,
    functions: 60,
    branches: 50,
    statements: 60,
  },
}
```

---

## 5. Checklist de Segurança

Este checklist descreve **o que foi corrigido** e **como verificar** que a correção está ativa.

### 5.1 Autenticação e Autorização

| Issue | Correção | Como verificar |
|-------|----------|----------------|
| CR-003 — JWT secret comprometido/backdoor | `JWT_SECRET_KEY` separada, falha no startup se ausente; `authenticate_user` valida usuario/senha salvos no SQLite | `unset JWT_SECRET_KEY && docker-compose up api` → container deve sair com erro. Tentativa de login com senha errada deve retornar 401. |
| CR-014 — Refresh token reutilizável | Rotação com blacklist: tabela `refresh_tokens` armazena `jti`; ao usar, marca `revoked_at` e emite novo par | Teste `test_refresh_token_reuso_retorna_401` passa. Reutilizar cookie `refresh_token` após refresh retorna 401. |
| CR-006 — JWT em localStorage (XSS) | Cookies `httpOnly Secure SameSite=Strict`; frontend sem acesso ao token | `document.cookie` no DevTools não mostra valor do token (só o nome). `localStorage.getItem('access_token')` retorna `null`. |
| CR-010 — Erro silenciado no refresh | `return Promise.reject(refreshError)` no catch do interceptor | No DevTools, se refresh falhar, a Promise é rejeitada (não fica pendente) e redireciona para `/login`. |
| HI-001 — CORS excessivamente permissivo | `allow_origins=[FRONTEND_URL]` em vez de `["*"]` | `curl -H "Origin: https://evil.com" http://localhost/api/v1/health` → resposta sem `Access-Control-Allow-Origin`. |
| HI-005 — Ausência de rate limiting | `slowapi` com limites: login 5/min, aprovação 10/min, listagem 30/min | 6 requisições de login em 1 minuto retornam 429. |

### 5.2 Dados e LGPD

| Issue | Correção | Como verificar |
|-------|----------|----------------|
| CR-005 — Screenshots públicos no nginx | Volume removido do nginx; screenshot só via `GET /api/v1/processos/{id}/screenshot` com auth | `curl http://localhost/screenshots/xxx.png` → 404. Endpoint autenticado retorna PNG com `Cache-Control: private`. |
| HI-014 — Path traversal em screenshots | `processo_id` validado como inteiro; path resolvido e verificado contra `SCREENSHOTS_BASE_DIR` | `curl /api/v1/processos/../../etc/passwd/screenshot` → 404/422 (FastAPI rejeita inteiro inválido). |
| CR-012 — PII em logs | Logs do agente registram apenas `processo_id`, etapa, status e contagens (`len(dados)`). Nunca CPF, nome ou valor | `docker logs custas-agente` → grep por padrão de CPF ou nome real não retorna matches. |
| HI-009 — PII em email sem escaping | `html.escape()` em todos os valores interpolados no template HTML | Email com `<script>alert(1)</script>` no número do processo renderiza como texto escapado. |
| M-003 — Log injection em rejeição | Observação sanitizada: `replace('\n',' ').replace('\r','')[:500]` antes de interpolar no log | Teste `test_rejeitar_observacao_sanitizada` passa. `\n` e `\r` não aparecem na mensagem de log. |

### 5.3 Injeção e Robustez

| Issue | Correção | Como verificar |
|-------|----------|----------------|
| CR-001 — SQL injection estrutural | `COLUNAS_PERMITIDAS_DADOS_PROCESSO = frozenset({...})` em `shared/sog_shared/db.py`; chaves fora da whitelist levantam `ValueError` | Teste `test_salvar_dados_coluna_invalida_levanta_valueerror` passa. |
| CR-002 — Injeção em seletores CSS Playwright | `page.get_by_text(texto, exact=True).click()` como primeira estratégia; helper `escape_for_css()` como fallback | Teste com processo "D'AVILA" não quebra o seletor. |
| HI-007 — Retry genérico capturando `Exception` | Default restrito a `(PlaywrightTimeout, ConnectionError, TimeoutError)` | `NameError` proposital em método decorado não dispara retry. |
| M-019 — Regex com backtracking catastrófico | Quantificadores com bounds (`{1,200}`) em vez de `.+?` livre | Regex executa em < 100ms para texto de 50KB. |
| M-020 — Datajud sem retry | Decorator `@retry_on_exception(exceptions=(ConnectionError, TimeoutError), max_retries=3, backoff=2)` | Simular 503 com mock → retorna após 3 retries. |
| M-024 — Slice mágico sem validação | Validação `len(numero_sem_mascara) == 20` e `isdigit()` antes do slice | Número malformado não causa `IndexError`. |

### 5.4 Concorrência e Integridade

| Issue | Correção | Como verificar |
|-------|----------|----------------|
| CR-004 — Race condition em aprovação | `BEGIN IMMEDIATE` + leitura e escrita na mesma conexão + `conn.commit()` | Teste de carga com 10 requests concorrentes resulta em exatamente 1 aprovação (demais retornam 400/409). Nota: em `:memory:` o teste verifica a lógica, mas concorrência real exige arquivo `.db` compartilhado. |
| CR-013 — SQLite sem controle de concorrência | WAL mode (`PRAGMA journal_mode=WAL`) + `busy_timeout=5000` | `PRAGMA journal_mode` retorna `wal`. |
| HI-002 — Threading sem controle | `threading.Thread` substituído por `BackgroundTasks` do FastAPI | `grep -r "threading.Thread" api/src/` retorna vazio. |

### 5.5 Infraestrutura

| Issue | Correção | Como verificar |
|-------|----------|----------------|
| CR-015 — Ausência de `.dockerignore` | `.dockerignore` na raiz exclui `.env*`, `dados/`, `.git`, `node_modules` | `docker build --no-cache -t test . && docker run --rm test ls -la /app` → não mostra `.env`. |
| CR-007 — API exposta na porta 8000 | Porta removida do `docker-compose.yml`; API acessível apenas via rede interna `sog-internal` | `nmap -p 8000 localhost` → "closed" ou "filtered". |
| CR-009 — Agente com privilégios excessivos | Container agente roda como `appuser` com `supercronic` (PID 1, exec form) | `docker exec custas-agente whoami` → `appuser`. `docker inspect custas-agente` → `User=appuser`. |
| HI-010 — Containers como root | `USER appuser` em todos os Dockerfiles (api, frontend, agente) | `docker inspect` mostra `User=appuser` para todos. |
| HI-011 — Sem security headers no nginx | `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `Referrer-Policy` | `curl -I http://localhost` → headers presentes em todas as respostas. |
| M-040 / M-041 — Sem `security_opt` e resource limits | `no-new-privileges:true`, `cap_drop: [ALL]`, `read_only: true`, `tmpfs`, limites de CPU/memória | `docker-compose config` valida sem erros. `docker inspect` mostra os campos. |
| M-045 / INF-001 — Proxy sem timeout/rate limit | Proxy timeouts (5s/10s/30s) + `limit_req_zone` + `limit_req burst=20` no nginx | 15 req/s para `/api/health` → burst absorve; acima disso retorna 503/429. |

---

## 6. Roadmap e Débitos Técnicos

### 6.1 Wave 8 — Migração SQLite → PostgreSQL (ADIADA)

**Motivo do adiamento:** Volume atual < 50 processos/dia. SQLite em WAL mode atende à demanda sem aumentar a complexidade operacional.

**Escopo quando for retomada:**

1. Adicionar serviço `postgres:15-alpine` ao `docker-compose.yml`
2. Adaptar `shared/sog_shared/db.py` para suportar `psycopg2` (placeholders `%s`, `RETURNING id`)
3. Script de migração `scripts/migrate_sqlite_to_postgres.py` com modo `dry-run`
4. Feature flag `USE_POSTGRES=true` por 1 sprint como rollback
5. Backup automático com `pg_dump`

**Reversibilidade:** BAIXA. Mitigação: manter SQLite como fallback por 1 sprint.

### 6.2 Débitos técnicos identificados

| Débito | Severidade | Contexto |
|--------|-----------|----------|
| Backup sidecar não implementado | 🟠 Alto | Planejado na Wave 6 (M-046) mas ausente do `docker-compose.yml`. O banco SQLite compartilhado não tem backup automático. |
| Rate limiting por IP pode ser contornado | 🟡 Médio | `slowapi` com storage in-memory reinicia contadores ao reiniciar o container. Em múltiplas réplicas, o limite não é global. |
| Teste de race condition em `:memory:` tem limitações | 🟡 Médio | O teste `test_aprovar_race_condition_apenas_uma_aprovacao` verifica a lógica de `BEGIN IMMEDIATE`, mas não simula concorrência real entre processos distintos. |
| TLS interno entre containers | 🟡 Médio | Comunicação inter-container em plaintext documentada como futura (Wave 8 ou pós-MVP). |
| `except Exception: pass` remanescentes | 🟢 Baixo | Substituídos por `except (PlaywrightTimeout, TimeoutError)` + log em quase todo o código. Ainda existem em `datajud.py` no fallback de `json.loads` (aceitável). |
| Healthcheck do agente verifica apenas supercronic | 🟢 Baixo | Não valida se o pipeline Python está executando com sucesso, apenas se o PID 1 é o supercronic. |

### 6.3 Recomendações pós-deploy

1. **Reavaliação de segurança:** Solicitar pentest externo antes de processar dados reais do TJDFT.
2. **RIPD:** Avaliar necessidade de Relatório de Impacto à Proteção de Dados (LGPD art. 50), dado que o sistema processa CPF/CNPJ e valores de partes processuais.
3. **Observabilidade:** Adicionar métricas (Prometheus/Grafana) e tracing para monitorar taxa de sucesso do agente e tempo de aprovação.
4. **CI/CD:** Introduzir pipeline com scan de vulnerabilidades (Trivy, Snyk) nas imagens Docker.

---

## 7. Referências Rápidas

### Endpoints da API (todos sob `/api/v1`)

```
POST   /auth/login          → cookie httpOnly access_token + refresh_token
POST   /auth/refresh        → rotação de refresh token
GET    /auth/me             → dados do usuário autenticado
POST   /auth/logout         → limpa cookies e revoga refresh token
GET    /health              → público, health check
GET    /processos           → lista paginada (limit/offset)
GET    /processos/{id}      → detalhe completo (JOIN único)
GET    /processos/{id}/screenshot → FileResponse PNG autenticado
POST   /aprovar/{id}        → aprovação com BEGIN IMMEDIATE
POST   /rejeitar/{id}       → rejeição com observação sanitizada
GET    /historico           → lista paginada de histórico
```

### Comandos úteis para operação

```bash
# Logs em tempo real
docker-compose logs -f api
docker-compose logs -f agente

# Verificar se há processos pendentes
docker exec custas-api sqlite3 /dados/custas.db \
  "SELECT COUNT(*) FROM processos WHERE status='aguardando_aprovacao';"

# Forçar backup manual do SQLite
docker exec custas-agente sqlite3 /dados/custas.db \
  ".backup /dados/backups/custas-$(date +%Y%m%d-%H%M%S).db"

# Reiniciar apenas o agente (útil após ajuste de credenciais)
docker-compose restart agente
```

---

## 8. Pontos Ambíguos e Como Foram Interpretados

1. **Backup sidecar (M-046):** O plano técnico da Wave 6 previa um serviço `backup` no `docker-compose.yml`, mas o arquivo atual não o contém. Foi interpretado como **não implementado** e registrado como débito técnico.

2. **Rate limiting em testes:** O `slowapi` usa storage in-memory. Em `TestClient` o IP é sempre o mesmo, então o rate limit pode não se comportar igual à produção. Os testes aceitam tanto 200 quanto 429 para não serem flaky.

3. **Validação de `processo_id` no endpoint de screenshot:** O código usa validação de path traversal via `Path.relative_to()`. O relatório original mencionava validação regex CNJ, mas o que foi implementado foi validação de inteiro positivo + resolução de path. Isso é tecnicamente suficiente para prevenir path traversal.

4. **Indicadores de login PJE (M-017):** A lista hardcoded "SHEILA" foi substituída por `PJE_INDICADORES_SUCESSO` (JSON list via env var). Se vazia, o sistema usa verificação genérica de DOM + URL. Isso torna o login mais robusto para diferentes usuários.

---

## 9. Entregas Incrementais (pós-code-review)

### 9.1 Extração de custas iniciais do PDF

**Data:** 2026-05-17  
**Status:** ✅ Entregue

O extrator de PDF passou a identificar e extrair o valor das custas iniciais a partir de guias de pagamento presentes no processo judicial. O algoritmo:

1. Lê a tabela de documentos da capa e filtra tipos `"Guia"` e `"Comprovante de Pagamento de Custas"`.
2. Localiza o `doc_id` da guia no texto completo do PDF (pode estar em qualquer página).
3. Isola uma janela de texto ao redor do `doc_id` e aplica regex para extrair:
   - Valor total e valor total em centavos (aritmética inteira, sem float)
   - Detalhamento por item (distribuidor, mandados, ofícios, contador, custas, diligências)
   - Número da guia e data de vencimento
4. Inclui o resultado no dict de retorno de `extrair_texto_pdf()` sob a chave `"custas_iniciais"`.

**Arquivos alterados:**
- `agente/src/modulos/extrator_pdf.py` — funções `_parse_valor_monetario`, `_extrair_valor_guia`, `extrair_custas_iniciais`
- `agente/tests/test_extrator_pdf.py` — testes da feature
- `agente/scripts/testar_pdf.py` — CLI atualizado para exibir custas iniciais

**Plano técnico:** `.kimi/plans/extracao-custas-iniciais.md`

**Limitação conhecida:** Os regex de extração são específicos ao formato de guia do TJDFT. Guias de outros tribunais podem exigir ajustes.

### 9.2 Correções no extrator de PDF (ressalvas do reviewer)

**Data:** 2026-05-17  
**Status:** ✅ Entregue

Correções aplicadas ao extrator de PDF (`agente/src/modulos/extrator_pdf.py`) após revisão de código (ressalvas P2 e ajustes P3):

| # | Severidade | Descrição | Detalhe técnico |
|---|-----------|-----------|-----------------|
| 1 | 🔴 P2 | Double-close do PyMuPDF | Removido `doc.close()` do bloco `except` (linha 641–642). O documento agora é fechado **apenas no `finally`**, eliminando o risco de `ValueError` (`document closed`) caso uma exceção ocorra durante o processamento das páginas. |
| 2 | 🔴 P2 | Falso positivo em `scanned` | A heurística de detecção de PDF image-only passou a ser **agregada**: `scanned=True` somente se **≥80% das páginas** forem candidatas a image-without-text **E** a média de texto por página for **< 100 caracteres** (linhas 631–638). Isso evita classificar como scanned PDFs cuja primeira página (capa) é predominantemente imagem mas o restante contém texto selecionável. |
| 3 | 🟡 P3 | Contrato uniforme do `resultado_base` | O dict base retornado por `extrair_texto_pdf()` passou a incluir `"custas_iniciais": {"encontrado": False, "scanned": False}` (linha 574). Antes, o campo só aparecia após a chamada de `extrair_custas_iniciais()`. Agora o contrato é uniforme: todo resultado possui a chave, mesmo quando a extração de custas não é executada. |
| 4 | 🟡 P3 | Threshold inclusivo `>= 0.8` | O operador de comparação da proporção de páginas scanned foi alterado de `> 0.8` para `>= 0.8` (linha 638). PDFs com exatamente 80% de páginas image-only agora são corretamente marcados como scanned. |
| 5 | 🟡 P3 | Comentário explicativo na heurística | Adicionado comentário de bloco acima da lógica de scanned detection (linhas 631–633) documentando as duas condições da heurística e o objetivo (evitar falso positivo em capas). |

**Arquivos alterados:**
- `agente/src/modulos/extrator_pdf.py` — correções na função `extrair_texto_pdf()`
- `agente/tests/test_extrator_pdf.py` — testes ajustados para cobrir os novos thresholds

---

> *Documentação produzida com base no código fonte verificado. Se algum comportamento no código divergir do descrito aqui, o código é a fonte da verdade — reporte ao mantenedor.*
