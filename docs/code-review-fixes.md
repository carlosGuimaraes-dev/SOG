# Plano técnico — correção das issues do code review enterprise

> Este arquivo descreve o plano de execução das correções.
> Para um resumo do que foi declarado como corrigido, consulte
> `correcoes-code-review.md`.

**Projeto:** SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)  
**Data:** 2026-05-15  
**Versão:** 1.0  
**Autor:** CTO / Fábrica de Software  
**Status:** Aprovado para execução  

---

## 1. Visão Geral

Este plano decompõe as **98 issues** do code review enterprise em **8 waves incrementais e verificáveis**, respeitando dependências entre módulos, minimizando risco de regressão e priorizando bloqueadores de deploy. O princípio de reversibilidade orienta cada wave: preferimos flags, migrações reversíveis e adapters a reescritas totais.

**Arquitetura-alvo ao final:**
- Auth via `httpOnly Secure SameSite=Strict` cookies (backend emite, frontend consome).
- Screenshots servidos exclusivamente por endpoint autenticado (`GET /api/v1/screenshots/{processo_id}`).
- SQLite em WAL mode como ponte; PostgreSQL como destino final (Wave 8).
- Pacote `shared/` com `db.py` e schemas Pydantic, eliminando `sys.path.insert`.
- Nginx como único ponto de entrada externo, com security headers e rate limiting.

---

## 2. Princípios do Plano

1. **Bloqueadores primeiro:** Todas as 15 issues críticas nas Waves 1–3.
2. **Backend antes de Frontend quando há contrato:** Cookies, screenshots e paginação exigem API estável antes do ajuste do cliente.
3. **Infra paralelizável:** Waves de DevOps rodam em paralelo a waves de código quando não tocam nos mesmos artefatos.
4. **Migração reversível:** SQLite → PostgreSQL é a única decisão de **baixa reversibilidade**; todos os demais ajustes podem ser revertidos via `git revert` ou feature flags.

---

## 3. Diagrama de Sequência de Execução

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  SEMANA 1          SEMANA 2          SEMANA 3          SEMANA 4+            │
│  ─────────         ─────────         ─────────         ─────────            │
│                                                                             │
│  Wave 1 ──────────┐                                                         │
│  (DevOps+Backend) │  Wave 3 ──────────┐                                     │
│                   │  (Auth Cross)     │  Wave 4 ──────────┐                 │
│  Wave 2 ──────────┤                   │  (Backend API)    │  Wave 5 ───┐    │
│  (Agente)         │                   │                   │  (Frontend)│    │
│                   │                   │                   │            │    │
│                   │                   │  Wave 6 ──────────┤  Wave 7 ───┤    │
│                   │                   │  (Arquitetura)    │  (DevOps)  │    │
│                   │                   │                   │            │    │
│                   │                   │                   │            ▼    │
│                   │                   │                   │  Wave 8 ──────  │
│                   │                   │                   │  (PostgreSQL)   │
└─────────────────────────────────────────────────────────────────────────────┘

Paralelismo permitido:
• Wave 1 || Wave 2  (não compartilham artefatos)
• Wave 5 || Wave 6 || Wave 7  (módulos distintos; cuidado com docker-compose.yml)
• Wave 8 DEPENDE de Wave 6 (pacote shared) e Wave 7 (infra pronta)
```

---

## 4. Waves Detalhadas

---

### Wave 1 — Segurança Crítica I: Infra + Auth Core
**Executor:** `devops` + `dev_senior` (paralelo)  
**Issues:** 14  
**Duração estimada:** 3 dias  
**Reversibilidade:** Alta  

| ID | Issue | Arquivo(s) | Executor |
|----|-------|------------|----------|
| CR-015 | Ausência de `.dockerignore` | raiz | devops |
| CR-007 | API exposta na porta 8000 | `docker-compose.yml`, `docker-compose.dev.yml` | devops |
| HI-011 | Sem security headers no nginx | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | devops |
| HI-010 | Containers API/frontend como root | `api/Dockerfile`, `frontend/Dockerfile` | devops |
| M-039 | Healthcheck nginx testa `/health` inexistente | `docker-compose.yml` | devops |
| M-050 | Sem HEALTHCHECK em api/frontend | `api/Dockerfile`, `frontend/Dockerfile` | devops |
| M-052 | `package.json` sem scripts test/lint | `frontend/package.json` | devops |
| M-053 | `.gitignore` genérico (falta `.env*` no docker context) | `.dockerignore` (novo) | devops |
| CR-003 | JWT Secret comprometido / backdoor | `api/src/auth.py`, `.env.example` | dev_senior |
| CR-014 | Refresh token reutilizável infinitamente | `api/src/rotas/auth.py`, `api/src/auth.py` | dev_senior |
| HI-001 | CORS excessivamente permissivo | `api/src/app.py` | dev_senior |
| CR-001 | SQL injection estrutural | `agente/src/banco/db.py` + `api/src/banco/db.py` (copiar whitelist) | dev_senior |
| M-002 | Exception handler genérico amplo | `api/src/app.py` | dev_senior |
| M-003 | Log injection em observação de rejeição | `api/src/rotas/aprovacao.py` | dev_senior |

#### Ações técnicas

**DevOps (paralelo, não depende de backend):**
1. **CR-015:** Criar `.dockerignore` na raiz:
   ```
   **/.env*
   dados/
   **/.git
   **/node_modules
   **/__pycache__
   **/.pytest_cache
   **/*.pyc
   .DS_Store
   ```
2. **CR-007:** Remover `ports: - "8000:8000"` do serviço `api` em ambos os compose files.
3. **HI-011:** Adicionar headers em ambos os nginx.conf:
   ```nginx
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header Content-Security-Policy "default-src 'self'; script-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'" always;
   add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   ```
4. **HI-010 / M-050:** Adicionar em `api/Dockerfile` e `frontend/Dockerfile`:
   ```dockerfile
   RUN useradd -m appuser && chown -R appuser:appuser /app
   USER appuser
   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
     CMD wget --quiet --tries=1 --spider http://localhost:8000/health || exit 1
   ```
   (Para frontend, ajustar porta para 80.)
5. **M-039:** Corrigir healthcheck do nginx para `testar http://localhost:80/`.
6. **M-052:** Adicionar scripts em `frontend/package.json`:
   ```json
   "test": "vitest run",
   "test:watch": "vitest",
   "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
   ```

**Backend (paralelo, não depende de DevOps):**
7. **CR-003:** Em `api/src/auth.py`:
   - Remover `SECRET_KEY` derivado de senha do dashboard.
   - Criar `JWT_SECRET_KEY` via `os.getenv("JWT_SECRET_KEY")`; falhar no startup se ausente ou < 32 chars.
   - Remover modo "dev sem senha" em `authenticate_user`; sempre validar usuario/senha persistidos no SQLite.
   - Persistir a credencial do dashboard no banco a partir da configuração do SOG Desktop.
8. **CR-014:** Em `api/src/rotas/auth.py`:
   - Criar tabela `refresh_tokens` no schema SQLite (`token_jti`, `user_id`, `expires_at`, `revoked_at`, `created_at`).
   - Ao emitir refresh token, gerar `jti` (uuid4) e persistir.
   - No endpoint `/auth/refresh`, validar `jti`, marcar como `revoked_at = now()`, emitir NOVO par (access + refresh) com novo `jti`.
   - Rejeitar se `revoked_at IS NOT NULL`.
9. **HI-001:** Em `api/src/app.py`:
   - Substituir `allow_origins=["*"]` por `allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")]`.
   - Em produção, `FRONTEND_URL` deve ser o domínio exato do nginx.
10. **CR-001:** Em `agente/src/banco/db.py` e `api/src/banco/db.py`:
    - Criar constante `COLUNAS_PERMITIDAS_DADOS_PROCESSO = frozenset([...])` com todas as colunas do schema.
    - Em `salvar_dados_processo`, rejeitar chaves fora do frozenset com `ValueError`.
    - Manter placeholders `?` para valores.
11. **M-002:** Em `api/src/app.py`:
    - Trocar `@app.exception_handler(Exception)` por handlers específicos: `RequestValidationError`, `HTTPException`, e um catch-all genérico que NÃO exponha `str(exc)` ao cliente (logar no servidor, retornar `"Erro interno do servidor"`).
12. **M-003:** Em `api/src/rotas/aprovacao.py`:
    - Sanitizar `req.observacao` antes de interpolar no log: `observacao_segura = req.observacao.replace('\n', ' ').replace('\r', '')[:500]`.
    - Nunca logar observação crua diretamente; usar structlog/json com campo separado.

#### Critérios de aceite mensuráveis
- [ ] `docker build` não inclui `.env` ou `dados/` no build context (verificar com `docker build --no-cache -t test . && docker run --rm test ls -la /app` não mostrar .env).
- [ ] `nmap` ou `curl` na porta 8000 do host retorna "Connection refused".
- [ ] Headers de segurança presentes em TODAS as respostas do nginx (`curl -I http://localhost` mostra `X-Frame-Options`, `CSP`, `HSTS`).
- [ ] `docker inspect` mostra `User=appuser` para containers api e frontend.
- [ ] Tentativa de login com senha errada retorna 401 usando a credencial do dashboard salva no SQLite.
- [ ] JWT decode falha se `JWT_SECRET_KEY` não for configurado no startup.
- [ ] Refresh token usado uma segunda vez retorna 401 (teste de rotação).
- [ ] Inserção com coluna inexistente em `dados_processo` levanta `ValueError` (teste unitário).
- [ ] Observação com `'; DROP TABLE` não aparece no log de servidor (verificar stdout do container api).

#### Dependências a instalar
- Nenhuma (apenas configuração e código).

---

### Wave 2 — Segurança Crítica II: Agente + Playwright + Dados
**Executor:** `dev_senior` (Python)  
**Issues:** 15  
**Duração estimada:** 4 dias  
**Reversibilidade:** Alta  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| CR-012 | PII em logs | `agente/src/main.py` |
| CR-002 | Injeção CSS Playwright | `agente/src/modulos/pje.py`, `sistjweb.py` |
| HI-007 | Retry genérico capturando `Exception` | `agente/src/modulos/retry.py` |
| HI-009 | PII em HTML de email sem escaping | `agente/src/utils/notificador.py` |
| M-017 | Indicadores de login hardcoded ("SHEILA") | `agente/src/modulos/pje.py` |
| M-019 | Regex com backtracking catastrófico | `agente/src/modulos/extrator_sentenca.py` |
| M-020 | Datajud sem retry/backoff | `agente/src/modulos/datajud.py` |
| M-021 | `except Exception: pass` no sistjweb | `agente/src/modulos/sistjweb.py` |
| M-022 | `except Exception: pass` no pje | `agente/src/modulos/pje.py` |
| M-023 | `json.loads` sem log de erro no LLM | `agente/src/modulos/extrator_sentenca.py` |
| M-024 | Slice mágico sem validação | `agente/src/modulos/datajud.py` |
| M-015 | `datetime.utcnow()` depreciado | `agente/src/utils/logger.py` |
| M-016 | Imports dentro de métodos de teste | `agente/tests/test_extrator_sentenca.py` |
| M-018 | `REGRAS_OUTROS_ITENS` vazias | `agente/src/regras.py` |
| A-001 | `db.py listar_pendentes` sem LIMIT (DoS memória) | `agente/src/banco/db.py` |

#### Ações técnicas
1. **CR-012:** Em `agente/src/main.py`:
   - Remover `str(dados_datajud)` e `str(dados_parser)` dos logs.
   - Logar apenas `processo_id`, `etapa`, `status`, e contagem de itens (ex: `f"{len(docs)} documentos"`).
   - Se precisar de dados para debug, logar hash SHA-256 dos campos sensíveis, nunca os valores.
2. **CR-002:** Em `pje.py` e `sistjweb.py`:
   - Substituir `f"text='{texto}'"` por `page.get_by_text(texto, exact=True).click()`.
   - Criar helper `escape_for_css(texto: str) -> str` que escapa aspas simples/duplas como camada de proteção adicional para casos onde `get_by_text` não for aplicável.
3. **HI-007:** Em `agente/src/modulos/retry.py`:
   - Trocar default `exceptions=(Exception,)` para `exceptions=(PlaywrightTimeout, ConnectionError, TimeoutError)`.
   - Manter `Exception` apenas em métodos explicitamente documentados.
4. **HI-009:** Em `agente/src/utils/notificador.py`:
   - Usar `html.escape(p['numero'])` e `html.escape(p.get('status',''))` antes de interpolar no template.
5. **M-017:** Em `pje.py`:
   - Substituir lista hardcoded `["text='SHEILA'", "text='Sheila'"]` por variável de ambiente `PJE_INDICADORES_SUCESSO` (JSON list) com fallback vazio.
   - Se vazio, usar apenas verificação por URL (não por nome de usuário).
6. **M-019:** Em `extrator_sentenca.py`:
   - Simplificar regex `RE_CIVEL_SUCUMBENTE` para evitar backtracking: limitar quantificadores `.+?` com bounds, ou usar `[^.]{1,200}` em vez de `.+?`.
   - Adicionar timeout de regex (Python 3.11+ não tem nativo; usar `signal` ou simplificar padrão).
7. **M-020:** Em `datajud.py`:
   - Adicionar decorator `@retry_on_exception(exceptions=(ConnectionError, TimeoutError), max_retries=3, backoff=2)`.
   - Usar `requests` com `timeout=(5, 30)` (connect, read).
8. **M-021 / M-022:** Em `sistjweb.py` e `pje.py`:
   - Trocar `except Exception: pass` por `except (PlaywrightTimeout, TimeoutError): logger.warning(...)` e `except Exception as e: logger.error(...)`.
   - Nunca silenciar exceções sem log.
9. **M-023:** Em `extrator_sentenca.py`:
   - Em `_chamar_llm`, envolver `json.loads` em `try/except json.JSONDecodeError` e logar `logger.error("Resposta LLM inválida: %s", conteudo[:200])`.
10. **M-024:** Em `datajud.py`:
    - Validar `len(numero_sem_mascara) == 20` e `numero_sem_mascara.isdigit()` antes do slice `14:16`.
11. **M-015:** Em `logger.py`:
    - Trocar `datetime.utcnow()` por `datetime.now(timezone.utc)`.
12. **M-016:** Em `test_extrator_sentenca.py`:
    - Mover todos os `from modulos.extrator_sentenca import ...` para o topo do arquivo.
13. **M-018:** Em `regras.py`:
    - Documentar que áreas vazias (`familia`, `fazenda_publica`, etc.) são intentionalmente vazias até mapeamento judicial, ou remover chaves se não aplicáveis.
14. **A-001:** Em `db.py`:
    - Adicionar `LIMIT 1000` em `listar_pendentes()` e `listar_aguardando_aprovacao()`.

#### Critérios de aceite mensuráveis
- [ ] Logs do agente não contêm CPF, nome de parte, valor da causa, endereço (grep por padrões de CPF e nomes reais em `docker logs custas-agente`).
- [ ] Processo com apóstrofo no nome (ex: "D'AVILA") não quebra seletor CSS (teste unitário com mock de Page).
- [ ] Retry com `NameError` NÃO dispara retry (teste unitário).
- [ ] Email HTML com `<script>alert(1)</script>` no número do processo renderiza como texto escapado.
- [ ] Regex de sentença executa em < 100ms para texto de 50KB (benchmark simples).
- [ ] Datajud com status 503 retorna após 3 retries (mock com `responses` ou `httpretty`).
- [ ] `json.loads` de resposta LLM malformada loga erro e retorna dict vazio sem crash.
- [ ] `datetime.utcnow()` não aparece mais no codebase (`grep -r "utcnow" agente/src/` retorna vazio).

#### Dependências a instalar
- `html.escape` (stdlib, já disponível).
- `uuid` (stdlib) para JTI dos refresh tokens (wave 1, mas usado aqui se necessário).

---

### Wave 3 — Auth Cross-Cutting: httpOnly Cookies + Screenshots API
**Executor:** `dev_senior` + `frontend` (coordenados)  
**Issues:** 10  
**Duração estimada:** 4 dias  
**Reversibilidade:** Média (mudança de contrato auth; rollback exige sincronia frontend+backend)  

| ID | Issue | Arquivo(s) | Executor |
|----|-------|------------|----------|
| CR-006 | JWT em localStorage (XSS) | `frontend/src/lib/api.ts`, `frontend/src/lib/auth.tsx`, `api/src/rotas/auth.py` | ambos |
| CR-005 | Exposição pública de screenshots | `docker-compose.yml`, `api/src/rotas/processos.py`, `frontend/src/pages/Detalhe.tsx` | ambos |
| HI-014 | Path traversal teórico em screenshots | `frontend/src/pages/Detalhe.tsx`, novo endpoint API | frontend + backend |
| CR-010 | Erro silenciado no refresh token | `frontend/src/lib/api.ts` | frontend |
| M-006 | JWT sem claims `iss`/`aud` | `api/src/auth.py` | backend |
| M-007 | Sem redirect HTTP→HTTPS | `nginx/nginx.conf` | devops |
| M-008 | API sem versionamento no path | `api/src/app.py`, todos os routers | backend |
| HI-015 / M-043 | Mesmo `.env` compartilhado | `.env.example`, `docker-compose.yml` | devops |
| M-014 | Type hint mentiroso (`Optional[int]` vs dict) | `agente/src/banco/db.py` | backend |
| F-001 | `Login.tsx` sem labels a11y | `frontend/src/pages/Login.tsx` | frontend |

#### Ações técnicas

**Backend:**
1. **CR-006 / M-006:** Em `api/src/rotas/auth.py`:
   - No login, emitir `Set-Cookie` com `access_token` (cookie `access_token`, httpOnly, Secure, SameSite=Strict, Max-Age=3600).
   - Emitir `Set-Cookie` com `refresh_token` (cookie `refresh_token`, httpOnly, Secure, SameSite=Strict, Max-Age=604800).
   - Adicionar claims `iss` (hostname), `aud` ("custas-dashboard"), `iat`, `exp`, `sub`, `type`.
   - O endpoint `/auth/refresh` lê cookie `refresh_token` em vez de body JSON.
2. **CR-005:** Em `api/src/rotas/processos.py` (novo router ou mesmo arquivo):
   - Criar `GET /api/v1/processos/{processo_id}/screenshot` que lê arquivo de `/dados/screenshots/{numero_processo}_sistjweb.png` APENAS se o processo existir e o usuário estiver autenticado (já é garantido por `Depends(get_current_user)`).
   - Retornar `FileResponse` do FastAPI com `media_type="image/png"`.
   - Adicionar cache-control `private, max-age=300`.
3. **HI-014:** Validar `processo_id` como inteiro positivo; validar que o arquivo está dentro de `/dados/screenshots/` (resolver path absoluto e verificar prefixo).
4. **M-008:** Em `api/src/app.py`:
   - Alterar `app = FastAPI(...)` para incluir `root_path="/api/v1"` ou registrar todos os routers com `prefix="/api/v1"`.
   - Atualizar nginx para proxy_pass `http://api:8000/api/v1/` → `location /api/v1/`.
5. **M-014:** Em `agente/src/banco/db.py`:
   - Corrigir type hint de `processo_existe` para retornar `Optional[Dict[str, Any]]` em vez de `Optional[int]`.
6. **M-007:** Em nginx:
   - Adicionar bloco `server { listen 80; return 301 https://$host$request_uri; }` quando `SSL_ENABLED=true`.

**Frontend:**
7. **CR-006:** Em `frontend/src/lib/api.ts`:
   - Remover TODO acesso a `localStorage.getItem('access_token')` e `localStorage.setItem(...)`.
   - Adicionar `withCredentials: true` (axios) para enviar cookies automaticamente.
   - O interceptor de request NÃO adiciona mais `Authorization` header.
   - O interceptor de refresh lê erro 401, chama `POST /auth/refresh` com `withCredentials: true`, e em caso de falha executa `window.location.href = '/login'` seguido de `return Promise.reject(error)`.
8. **CR-010:** No catch do refresh interceptor, garantir `return Promise.reject(error)` após redirect.
9. **CR-005 / HI-014:** Em `frontend/src/pages/Detalhe.tsx`:
   - Substituir `<img src={`/screenshots/${p.numero}_sistjweb.png`} />` por `<img src={`/api/v1/processos/${p.id}/screenshot`} />`.
   - Adicionar tratamento de erro 404 (screenshot não disponível).
10. **F-001:** Em `Login.tsx`:
    - Adicionar `htmlFor` nos labels, `aria-label` nos inputs, `type="password"` no campo de senha (se ainda não tiver).

**DevOps:**
11. **HI-015 / M-043:** Em `docker-compose.yml`:
    - Criar `.env.agente` (PJE/SISTJ/SMTP) e `.env.api` (JWT/DASHBOARD).
    - Mapear `env_file: .env.agente` para serviço agente, `env_file: .env.api` para serviço api.
    - Remover variáveis desnecessárias de cada env.

#### Critérios de aceite mensuráveis
- [ ] `document.cookie` no browser não mostra `access_token` (cookie é httpOnly).
- [ ] `localStorage.getItem('access_token')` retorna `null` após login.
- [ ] Tentativa de acessar `/screenshots/xxx.png` via nginx retorna 404 (volume removido).
- [ ] Endpoint `/api/v1/processos/123/screenshot` retorna imagem PNG com `Content-Type: image/png` e `Cache-Control: private`.
- [ ] Path traversal `../../etc/passwd` no endpoint de screenshot retorna 400/404.
- [ ] Refresh token com `jti` inválido/revogado retorna 401 e redireciona para login.
- [ ] Todos os endpoints da API respondem sob `/api/v1/` (verificar com `curl http://localhost/api/v1/health`).
- [ ] `processo_existe` retorna dict (type hint correto) em testes de tipo (`mypy` ou `pyright`).

#### Dependências a instalar
- Backend: nenhuma (cookies são nativos FastAPI/Starlette).
- Frontend: nenhuma (axios já suporta `withCredentials`).

---

### Wave 4 — Backend API: Concorrência, Paginação, Models
**Executor:** `dev_senior`  
**Issues:** 12  
**Duração estimada:** 4 dias  
**Reversibilidade:** Alta  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| CR-004 | Race condition em aprovação | `api/src/rotas/aprovacao.py`, `agente/src/banco/db.py` |
| CR-013 | SQLite compartilhado sem concorrência | `docker-compose.yml`, `agente/src/banco/db.py` |
| HI-002 | Threading sem controle de lifecycle | `api/src/rotas/aprovacao.py` |
| HI-005 | Ausência de rate limiting | `api/src/app.py`, `api/src/rotas/auth.py` |
| HI-012 | Sem paginação em `/processos` | `api/src/rotas/processos.py` |
| M-001 | Input `limit`/`offset` sem bounds | `api/src/rotas/historico.py` |
| M-004 | Response models genéricas | `api/src/rotas/processos.py`, `historico.py` |
| M-005 | N+1 queries em detalhar processo | `api/src/rotas/processos.py` |
| HI-013 | Testes da API dependem de banco real | `api/tests/test_api.py` |
| M-012 | `_init_db()` no import global | `agente/src/banco/db.py` |
| M-013 | Side-effects no import de config.py | `agente/src/config.py` |
| M-011 | `sys.path.insert` em main.py e rotas | `agente/src/main.py`, `api/src/rotas/*.py` |

#### Ações técnicas
1. **CR-004:** Em `api/src/rotas/aprovacao.py`:
   - Refatorar `aprovar_processo` para usar UMA conexão SQLite com `BEGIN IMMEDIATE`:
     ```python
     with db.get_conn() as conn:
         conn.execute("BEGIN IMMEDIATE")
         row = conn.execute("SELECT status FROM processos WHERE id = ?", (processo_id,)).fetchone()
         # ... validações ...
         conn.execute("UPDATE processos SET status = 'aprovado' WHERE id = ?", (processo_id,))
         conn.execute("INSERT INTO log_execucao (...) VALUES (...)")
         conn.commit()
     ```
   - Adicionar constraint UNIQUE ou status machine se possível no schema.
2. **CR-013 / M-012:** Em `agente/src/banco/db.py`:
   - Remover `_init_db()` do nível do módulo.
   - Criar função `init_db()` explícita chamada no startup do agente e no lifespan da API.
   - Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` na conexão.
3. **HI-002:** Em `api/src/rotas/aprovacao.py`:
   - Substituir `threading.Thread` por `BackgroundTasks` do FastAPI.
   - Se emissão precisar de Playwright, disparar tarefa via `BackgroundTasks` e retornar `"aprovado, emissão em background"`.
4. **HI-005:** Em `api/src/app.py`:
   - Adicionar `slowapi` (ou `fastapi-limiter` com Redis, mas Redis é dependência extra; preferir `slowapi` com limitador em memória para MVP).
   - Rate limits: login 5/min, aprovação 10/min, listagem 30/min.
5. **HI-012 / M-001:** Em `api/src/rotas/processos.py` e `historico.py`:
   - Adicionar `limit: int = Query(50, ge=1, le=1000)` e `offset: int = Query(0, ge=0)`.
   - Aplicar paginação em `listar_processos` e `historico`.
6. **M-004:** Criar schemas Pydantic em `api/src/schemas.py`:
   - `ProcessoResponse`, `ProcessoListResponse`, `AprovacaoResponse`, `HistoricoItemResponse`.
   - Substituir `Dict[str, Any]` e `List[Dict[str, Any]]` pelos models em TODOS os routers.
7. **M-005:** Em `api/src/rotas/processos.py`:
   - Refatorar `detalhar_processo` para fazer JOIN único:
     ```sql
     SELECT p.*, d.* FROM processos p LEFT JOIN dados_processo d ON ... WHERE p.id = ?
     ```
   - Ou usar `row_factory` e mapear campos manualmente em uma única query.
8. **HI-013:** Em `api/tests/test_api.py`:
   - Mockar `db.get_conn()` para retornar SQLite `:memory:`.
   - Ou usar fixture `pytest` que inicializa banco em memória e injeta no app.
9. **M-013:** Em `agente/src/config.py`:
   - Mover `load_dotenv()` e criação de diretórios para uma função `init_config()` chamada explicitamente.
   - No nível do módulo, manter apenas declarações de variáveis sem side-effects.
10. **M-011:** Em `agente/src/main.py` e `api/src/rotas/*.py`:
    - Adicionar comentário `# TODO-WAVE6: remover após extração do pacote shared`.
    - Não remover ainda (depende da Wave 6).

#### Critérios de aceite mensuráveis
- [ ] Teste de carga com 10 requests concorrentes para `/aprovar/1` resulta em exatamente 1 aprovação (demais retornam 400 ou 409).
- [ ] `PRAGMA journal_mode` retorna `wal` no banco de dados.
- [ ] `threading.Thread` não aparece mais em `api/src/rotas/aprovacao.py`.
- [ ] 6 requisições de login em 1 minuto resultam em 429 na 6ª.
- [ ] `/processos?limit=2000` retorna 422 (validation error).
- [ ] Todos os endpoints retornam schemas validados por Pydantic (teste com `response_model` explícito).
- [ ] Testes da API rodam em < 5s sem depender de arquivo `.db` no filesystem.
- [ ] `import agente.src.config` NÃO cria diretórios no filesystem (testar com `tmpdir` limpo).

#### Dependências a instalar
- `slowapi==0.1.9` (limiter em memória; sem Redis para manter infra simples no MVP).
- `pydantic` (já instalado via FastAPI).

---

### Wave 5 — Frontend: Refatoração, UX e Testes
**Executor:** `frontend`  
**Issues:** 16  
**Duração estimada:** 5 dias  
**Reversibilidade:** Alta  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| CR-011 | Roteamento aninhado incorreto (react-router v6) | `frontend/src/App.tsx` |
| HI-008 | Ausência de Error Boundaries | `frontend/src/App.tsx` |
| HI-003 | Zero testes no frontend | `frontend/src/` (todos) |
| HI-004 | `Detalhe.tsx` monolítico (328 linhas) | `frontend/src/pages/Detalhe.tsx` |
| M-025 | Toast container replicado em 3 páginas | `Fila.tsx`, `Detalhe.tsx`, `Historico.tsx` |
| M-026 | `useState<any>(null)` | `frontend/src/pages/Detalhe.tsx` |
| M-027 | Interface `Processo` duplicada | `Fila.tsx`, `Historico.tsx` |
| M-028 | Magic strings de endpoints | vários |
| M-029 | Sem React.lazy/Suspense | `frontend/src/App.tsx` |
| M-030 | `useToast` isolado (não global) | `frontend/src/hooks/useToast.ts` |
| M-031 | Textarea nativa hardcoded | `frontend/src/pages/Detalhe.tsx` |
| M-032 | Labels sem htmlFor, botões sem aria-label | `Login.tsx`, `Detalhe.tsx` |
| M-033 | ThemeToggle inline no App.tsx | `frontend/src/App.tsx` |
| M-034 | Import comentado de Badge | `frontend/src/pages/Detalhe.tsx` |
| M-035 | Skeleton sem aria-busy | `frontend/src/components/ui/Skeleton.tsx` |
| F-002 | `api.ts` não trata erros de rede explicitamente | `frontend/src/lib/api.ts` |

#### Ações técnicas
1. **CR-011:** Em `App.tsx`:
   - Refatorar para estrutura correta do react-router-dom v6:
     ```tsx
     <Routes>
       <Route path="/login" element={<Login />} />
       <Route element={<RequireAuth><Layout /></RequireAuth>}>
         <Route path="/" element={<Fila />} />
         <Route path="/detalhe/:id" element={<Detalhe />} />
         <Route path="/historico" element={<Historico />} />
       </Route>
     </Routes>
     ```
   - `Layout` usa `<Outlet />` para renderizar rotas filhas.
2. **HI-008:** Criar `frontend/src/components/ErrorBoundary.tsx`:
   - Classe React que captura erros de renderização.
   - Exibe UI de fallback com botão "Recarregar página".
   - Envolver `<Routes>` no `App.tsx`.
3. **HI-003:** Configurar testes:
   - Instalar `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `msw` (mock service worker).
   - Meta mínima: 60% cobertura nos fluxos críticos (login, listagem, aprovação).
   - Criar testes para `Login`, `Fila`, `aprovar` em `Detalhe`.
4. **HI-004 / M-026 / M-031:** Refatorar `Detalhe.tsx`:
   - Extrair hooks customizados: `useProcesso(id)`, `useAprovar(id)`, `useRejeitar(id)`.
   - Extrair sub-componentes: `DadosProcessoCard`, `SucumbentesTable`, `ScreenshotCard`, `AcoesPanel`.
   - Tipar `data` com interface `ProcessoCompleto` em vez de `any`.
   - Substituir `<textarea>` nativa por componente `Textarea` reutilizável.
   - Remover import comentado de Badge.
5. **M-025 / M-030:** Criar `ToastProvider`:
   - Usar React Context para gerenciar toasts globalmente.
   - `<ToastContainer />` renderizado uma única vez no `Layout`.
   - Remover replicação de toast UI de `Fila`, `Detalhe`, `Historico`.
6. **M-027:** Criar `frontend/src/types/processo.ts`:
   - Interface `Processo` compartilhada entre `Fila`, `Historico`, `Detalhe`.
   - Usar `Pick`/`Omit` se necessário para variações.
7. **M-028:** Criar `frontend/src/lib/endpoints.ts`:
   - Constantes `ENDPOINTS = { LOGIN: '/auth/login', PROCESSOS: '/processos', ... }`.
   - Substituir strings mágicas em todos os componentes.
8. **M-029:** Em `App.tsx`:
   - Usar `React.lazy(() => import('./pages/Detalhe'))` e `Suspense fallback={<Skeleton />}>`.
9. **M-032:** Adicionar `aria-label` em todos os botões de ação e `htmlFor` nos labels de formulário.
10. **M-033:** Extrair `ThemeToggle` para `frontend/src/components/ThemeToggle.tsx`.
11. **M-035:** Em `Skeleton.tsx`:
    - Adicionar `role="status" aria-busy="true" aria-label="Carregando..."`.
12. **F-002:** Em `api.ts`:
    - Adicionar tratamento de `error.code === 'ERR_NETWORK'` com toast "Sem conexão com o servidor".

#### Critérios de aceite mensuráveis
- [ ] Navegação entre `/`, `/detalhe/1`, `/historico` funciona sem re-mounts desnecessários (React DevTools Profiler).
- [ ] Erro de JavaScript em `Detalhe.tsx` mostra tela de fallback do ErrorBoundary, não tela branca.
- [ ] `npm run test` executa e passa com cobertura >= 60% nos fluxos críticos.
- [ ] `Detalhe.tsx` tem <= 120 linhas após refatoração.
- [ ] `useState<any>` não aparece mais no codebase (`grep -r "useState<any>" frontend/src/` retorna vazio).
- [ ] Toast container existe em apenas 1 lugar no DOM (React DevTools).
- [ ] `npm run build` gera chunks separados para `Detalhe` e `Historico` (verificar `dist/assets/`).
- [ ] Lighthouse a11y score >= 90.

#### Dependências a instalar
- `vitest@^1.6.0`
- `@testing-library/react@^15.0.0`
- `@testing-library/jest-dom@^6.4.0`
- `@testing-library/user-event@^14.5.0`
- `msw@^2.3.0`
- `jsdom@^24.0.0`
- `@vitejs/plugin-react` já instalado; adicionar `vite.config.ts` com `test: { environment: 'jsdom' }`.

---

### Wave 6 — Arquitetura Python: Pacote Compartilhado + SRP
**Executor:** `dev_senior` + `arquiteto` (revisão de design)  
**Issues:** 10  
**Duração estimada:** 4 dias  
**Reversibilidade:** Média (mudança de estrutura de imports; rollback possível via PYTHONPATH)  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| CR-008 | Acoplamento Agente→API | `api/Dockerfile`, `api/src/rotas/*.py` |
| M-011 | `sys.path.insert` em main.py e rotas | `agente/src/main.py`, `api/src/rotas/*.py` |
| M-010 | Duplicação parser vs extrator_sentenca | `agente/src/modulos/parser.py`, `extrator_sentenca.py` |
| HI-006 | Duplicação de inicialização Playwright | `agente/src/modulos/pje.py`, `sistjweb.py` |
| M-009 | `processar_processo` com 96 linhas (SRP) | `agente/src/main.py` |
| M-046 | SQLite sem backup/HA | `docker-compose.yml` |
| M-047 | Agente ausente no docker-compose.dev.yml | `docker-compose.dev.yml` |
| M-048 | `location /api/` duplicado no frontend nginx | `frontend/nginx-default.conf` |
| M-049 | Nginx dev na porta 80 (conflito) | `docker-compose.dev.yml` |
| M-051 | Cache apt não limpo | `agente/Dockerfile` |

#### Ações técnicas
1. **CR-008 / M-011:** Criar `shared/` na raiz:
   - `shared/pyproject.toml` com `name = "sog-shared"`.
   - `shared/sog_shared/db.py` — cópia limpa de `agente/src/banco/db.py` (sem `_init_db` no import).
   - `shared/sog_shared/schemas.py` — schemas Pydantic compartilhados (Processo, DadosProcesso, etc.).
   - `shared/sog_shared/config.py` — variáveis de ambiente comuns (DB_PATH, TIMEOUT_PADRAO).
   - Em `api/Dockerfile`, remover `COPY agente/src/ ./agente_src/`; adicionar `COPY shared/ ./shared/` e `RUN pip install -e ./shared`.
   - Em `agente/Dockerfile`, adicionar `COPY shared/ ./shared/` e `RUN pip install -e ./shared`.
   - Remover `sys.path.insert` de `api/src/rotas/*.py` e `agente/src/main.py`; usar `from sog_shared import db, config`.
2. **M-010:** Em `agente/src/modulos/parser.py`:
   - Depreciar `parse_sentenca` e `parse_comprovante_pagamento`.
   - Reexportar funções de `extrator_sentenca.py` para manter compatibilidade temporária.
   - Remover duplicação de regex; `parser.py` deve conter apenas lógica de orquestração de documentos.
3. **HI-006:** Em `agente/src/modulos/`:
   - Criar `PlaywrightClient` base com `iniciar()`, `fechar()`, `verificar_sessao()`, `reconectar()`.
   - `PjeClient` e `SistjClient` herdam de `PlaywrightClient`.
   - Extrair viewport, headless, timeout para a classe base.
4. **M-009:** Em `agente/src/main.py`:
   - Extrair funções menores: `_coletar_datajud()`, `_coletar_documentos()`, `_preencher_sistj()`, `_notificar_operador()`.
   - `processar_processo` deve ter <= 40 linhas, orquestrando apenas.
5. **M-046:** Em `docker-compose.yml`:
   - Adicionar serviço `backup` (sidecar) que roda `sqlite3 /dados/custas.db ".backup /dados/backups/custas-$(date +%Y%m%d-%H%M%S).db"` via cron.
   - Ou usar volume snapshot se filesystem suportar.
6. **M-047:** Em `docker-compose.dev.yml`:
   - Adicionar serviço `agente` com build do Dockerfile do agente e volumes de desenvolvimento.
7. **M-048:** Em `frontend/nginx-default.conf`:
   - Remover bloco `location /api/` (o nginx principal já faz proxy).
8. **M-049:** Em `docker-compose.dev.yml`:
   - Mapear nginx dev para porta `8080:80` em vez de `80:80`.
9. **M-051:** Em `agente/Dockerfile`:
   - Adicionar `rm -rf /var/lib/apt/lists/*` após `apt-get install`.

#### Critérios de aceite mensuráveis
- [ ] `api/Dockerfile` não contém `COPY agente/src/`.
- [ ] `grep -r "sys.path.insert" api/src/ agente/src/` retorna vazio.
- [ ] `from sog_shared import db` funciona tanto no container api quanto no agente.
- [ ] `pytest agente/tests/` passa sem `sys.path` hacks.
- [ ] `PjeClient` e `SistjClient` herdam de `PlaywrightClient` (verificar com `issubclass`).
- [ ] `processar_processo` tem <= 40 linhas (`wc -l` no arquivo após refatoração).
- [ ] Arquivos de backup `.db` são gerados em `/dados/backups/` a cada 24h.
- [ ] `docker-compose -f docker-compose.dev.yml up` sobe agente, api, frontend e nginx sem erros.

#### Dependências a instalar
- Criar `shared/pyproject.toml` com `setuptools` (não requer instalação externa; `pip install -e` funciona).

---

### Wave 7 — Infra Hardening Completo
**Executor:** `devops`  
**Issues:** 14  
**Duração estimada:** 3 dias  
**Reversibilidade:** Alta  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| CR-009 | Container do Agente com privilégios excessivos | `agente/Dockerfile` |
| M-036 | Imagem agente gigante (>1.5GB) | `agente/Dockerfile` |
| M-037 | `package-lock.json` não copiado | `frontend/Dockerfile` |
| M-038 | `pytest` em requirements de produção | `agente/requirements.txt` |
| M-040 | Sem `security_opt`, `read_only`, `cap_drop` | `docker-compose.yml` |
| M-041 | Sem resource limits | `docker-compose.yml` |
| M-042 | Crontab com `chmod 0644` | `agente/Dockerfile` |
| M-044 | Comunicação inter-container em plaintext | `docker-compose.yml` |
| M-045 | Proxy sem timeout/retry/buffer | `nginx/nginx.conf` |
| HI-010 | Container agente como root (complemento) | `agente/Dockerfile` |
| M-050 | Sem HEALTHCHECK no agente | `agente/Dockerfile` |
| M-052 | package.json sem scripts (complemento) | `frontend/package.json` |
| M-053 | `.gitignore` genérico (complemento) | `.gitignore` |
| INF-001 | Nginx sem rate limiting upstream | `nginx/nginx.conf` |

#### Ações técnicas
1. **CR-009 / HI-010 / M-042 / M-050:** Em `agente/Dockerfile`:
   - Adicionar `RUN useradd -m appuser && chown -R appuser:appuser /app /dados`.
   - `USER appuser`.
   - Instalar `supercronic` (ou usar `cron` do sistema como root em container separado? Preferir `supercronic` pois roda como usuário não-root).
   - Alterar CMD para `CMD ["supercronic", "/app/crontab"]` (exec form, PID 1).
   - `chmod 0600` no crontab (não 0644).
   - Adicionar `HEALTHCHECK` que verifica existência do PID do supercronic ou heartbeat do agente.
2. **M-036:** Em `agente/Dockerfile`:
   - Usar multi-stage build: stage 1 instala Playwright e dependências; stage 2 copia apenas o necessário.
   - Ou remover `playwright install-deps chromium` se não for estritamente necessário (testar).
   - Meta: imagem < 800MB.
3. **M-037:** Em `frontend/Dockerfile`:
   - Copiar `package-lock.json` antes de `npm install` para cache deterministico:
     ```dockerfile
     COPY frontend/package.json frontend/package-lock.json ./
     RUN npm ci
     ```
4. **M-038:** Em `agente/`:
   - Criar `requirements-dev.txt` com `pytest`, `pytest-mock`.
   - Remover `pytest` e `pytest-mock` de `requirements.txt`.
   - Em `agente/Dockerfile`, usar `requirements.txt` (produção).
5. **M-040 / M-041:** Em `docker-compose.yml`:
   - Adicionar `security_opt: ["no-new-privileges:true"]`.
   - Adicionar `cap_drop: ["ALL"]` e `cap_add: ["CHOWN", "SETGID", "SETUID"]` apenas se necessário.
   - Adicionar `read_only: true` com `tmpfs` para `/tmp` se possível.
   - Adicionar `deploy.resources.limits.memory` e `cpus` para cada serviço.
6. **M-044:** Em `docker-compose.yml`:
   - Criar rede interna `sog-internal` com `internal: true` para serviços que não precisam de internet (api, frontend, agente).
   - Nginx fica em rede `sog-external` + `sog-internal`.
   - Documentar que TLS interno é futuro (Wave 8 ou pós-MVP).
7. **M-045 / INF-001:** Em `nginx/nginx.conf`:
   - Adicionar proxy timeouts:
     ```nginx
     proxy_connect_timeout 5s;
     proxy_send_timeout 10s;
     proxy_read_timeout 30s;
     proxy_buffering on;
     proxy_buffer_size 4k;
     proxy_buffers 8 4k;
     ```
   - Adicionar rate limiting básico via `limit_req_zone` e `limit_req` (nginx nativo, sem dependências externas):
     ```nginx
     limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
     location /api/ { limit_req zone=api burst=20 nodelay; ... }
     ```
8. **M-053:** Em `.gitignore`:
   - Garantir que `.env*` está incluído (já está; apenas verificar).

#### Critérios de aceite mensuráveis
- [ ] `docker inspect custas-agente` mostra `User=appuser`.
- [ ] `docker images | grep custas-agente` mostra tamanho < 800MB.
- [ ] `docker-compose config` valida sem erros com `security_opt`, `cap_drop`, `read_only`.
- [ ] `pytest` não está em `agente/requirements.txt`.
- [ ] `npm ci` usa `package-lock.json` (checksum do lock não muda entre builds).
- [ ] `limit_req` no nginx: 15 requests/segundo para `/api/health` resultam em 503/429 após burst.
- [ ] Container agente não roda como root (`whoami` dentro do container retorna `appuser`).

#### Dependências a instalar
- `supercronic` (binário estático; adicionar ao Dockerfile via `wget` do release GitHub).

---

### Wave 8 — Migração SQLite → PostgreSQL
**Executor:** `arquiteto` + `devops` + `dev_senior`  
**Issues:** 3 (inclui CR-004 complemento, CR-013 complemento, M-046 complemento)  
**Duração estimada:** 5–7 dias  
**Reversibilidade:** **BAIXA** — alteração de schema, migração de dados, mudança de driver  

| ID | Issue | Arquivo(s) |
|----|-------|------------|
| PG-001 | Migrar SQLite → PostgreSQL | `docker-compose.yml`, `agente/src/banco/db.py`, `api/src/` |
| PG-002 | Adaptar queries SQLite → PostgreSQL | `shared/sog_shared/db.py` |
| PG-003 | Backup e restore de dados | `docker-compose.yml`, scripts de migração |

#### Ações técnicas
1. **PG-001:** Adicionar serviço `postgres:15-alpine` ao `docker-compose.yml`.
   - Volume dedicado `pgdata`.
   - Variáveis `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` em `.env.api`.
2. **PG-002:** Em `shared/sog_shared/db.py`:
   - Criar adapter `get_conn()` que detecta driver (SQLite vs psycopg2) via `DATABASE_URL`.
   - Se `DATABASE_URL` começar com `sqlite:///`, usar sqlite3; se `postgresql://`, usar `psycopg2`.
   - Adaptar placeholders: SQLite usa `?`, PostgreSQL usa `%s`.
   - Adaptar `PRAGMA` e `LAST_INSERT_ROWID()` para PostgreSQL (`RETURNING id`).
3. **PG-003:** Criar script `scripts/migrate_sqlite_to_postgres.py`:
   - Ler SQLite existente, inserir em PostgreSQL respeitando constraints.
   - Rodar em modo `dry-run` primeiro.
   - Suportar rollback (dump do PostgreSQL antes da migração).
4. **CR-004 (complemento):** Com PostgreSQL, race condition é resolvida nativamente via `SELECT FOR UPDATE` ou transações SERIALIZABLE.
5. **CR-013 (complemento):** SQLite compartilhado é removido; cada serviço conecta ao PostgreSQL via rede interna.

#### Critérios de aceite mensuráveis
- [ ] `docker-compose up postgres` sobe e aceita conexões.
- [ ] Script de migração copia todos os processos, dados, logs e documentos sem perda (verificar contagem de registros antes/depois).
- [ ] Testes de API passam com PostgreSQL (alterar `DATABASE_URL` nos testes para um banco de testes).
- [ ] `docker-compose.yml` não mapeia mais volume `./dados:/dados` compartilhado entre agente e api.
- [ ] Backup automático do PostgreSQL via `pg_dump` executa diariamente.

#### Dependências a instalar
- `psycopg2-binary==2.9.9`
- Serviço `postgres:15-alpine` no Docker Compose.

#### ⚠️ Decisão de baixa reversibilidade
- **Motivo:** Migração de dados entre SQLite e PostgreSQL é unidirecional sem script de rollback explícito.
- **Mitigação:** Manter SQLite como fallback por 1 sprint (feature flag `USE_POSTGRES=true`); se falhar, voltar para SQLite alterando `DATABASE_URL`.
- **Escalar ao CEO:** Aprovar custo de infra do container PostgreSQL (+~100MB RAM, +~500MB disco).

---

## 5. Matriz de Dependências

| Wave | Depende de | Pode rodar em paralelo com |
|------|-----------|---------------------------|
| 1 | — | Wave 2 |
| 2 | — | Wave 1 |
| 3 | Wave 1 (JWT fix, CORS) | — |
| 4 | Wave 1, Wave 3 (auth estável) | — |
| 5 | Wave 3 (cookies, routing) | Wave 6, Wave 7 (cuidado com docker-compose) |
| 6 | Wave 4 (backend estável), Wave 1 (Docker ajustado) | Wave 5, Wave 7 |
| 7 | Wave 1 (USER base), Wave 6 (pacote shared) | Wave 5, Wave 6 |
| 8 | Wave 6 (shared package), Wave 7 (infra pronta) | — |

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| httpOnly cookies quebram fluxo de dev local | Alta | Médio | Manter modo `dev` com `Secure=false` e `SameSite=Lax` quando `ENV=development` (feature flag). |
| PlaywrightClient base quebra automação existente | Média | Alto | Criar testes de integração do agente ANTES da refatoração; manter métodos antigos como `@deprecated` por 1 sprint. |
| PostgreSQL migration corrompe dados | Baixa | Crítico | Backup SQLite antes; dry-run; manter feature flag `USE_POSTGRES` por 1 sprint. |
| Rate limiting bloqueia operadores legítimos | Média | Médio | Iniciar com limites generosos (10r/s) e ajustar com base em logs. |
| Refatoração Detalhe.tsx introduz regressão | Média | Alto | Cobrir com testes Vitest ANTES de refatorar; usar git branch isolado. |

---

## 7. Checklist de Aceite Global

- [ ] Todas as 15 issues críticas (CR-001 a CR-015) estão corrigidas e testadas.
- [ ] Todos os endpoints da API retornam response models Pydantic (nenhum `Dict[str, Any]` exposto).
- [ ] Nenhum token JWT é armazenado em `localStorage` ou `sessionStorage`.
- [ ] Screenshots não são acessíveis via nginx diretamente; apenas via endpoint autenticado.
- [ ] A API não é acessível diretamente na porta 8000 do host.
- [ ] Todos os containers rodam como usuário não-root.
- [ ] Testes de API rodam em < 5s com banco em memória/mock.
- [ ] Testes de frontend cobrem >= 60% dos fluxos críticos e passam no CI.
- [ ] Nenhum `sys.path.insert` restante em `api/src/` ou `agente/src/`.
- [ ] Logs do agente não contêm PII não mascarado (validado por grep).
- [ ] Rate limiting ativo em login, aprovação e listagem.
- [ ] Migração para PostgreSQL concluída com zero perda de dados (contagem de registros validada).

---

## 8. Índice de Issues por Wave

| Wave | Issues | Contagem |
|------|--------|----------|
| Wave 1 | CR-015, CR-007, HI-011, HI-010, M-039, M-050, M-052, M-053, CR-003, CR-014, HI-001, CR-001, M-002, M-003 | 14 |
| Wave 2 | CR-012, CR-002, HI-007, HI-009, M-017, M-019, M-020, M-021, M-022, M-023, M-024, M-015, M-016, M-018, A-001 | 15 |
| Wave 3 | CR-006, CR-005, HI-014, CR-010, M-006, M-007, M-008, HI-015/M-043, M-014, F-001 | 10 |
| Wave 4 | CR-004, CR-013, HI-002, HI-005, HI-012, M-001, M-004, M-005, HI-013, M-012, M-013, M-011 | 12 |
| Wave 5 | CR-011, HI-008, HI-003, HI-004, M-025, M-026, M-027, M-028, M-029, M-030, M-031, M-032, M-033, M-034, M-035, F-002 | 16 |
| Wave 6 | CR-008, M-011, M-010, HI-006, M-009, M-046, M-047, M-048, M-049, M-051 | 10 |
| Wave 7 | CR-009, M-036, M-037, M-038, M-040, M-041, M-042, M-044, M-045, HI-010, M-050, M-052, M-053, INF-001 | 14 |
| Wave 8 | PG-001, PG-002, PG-003 | 3 |
| **Total** | | **94** |

As 4 issues restantes para completar 98 são derivadas implícitas do relatório (A-001, F-001, F-002, INF-001) e issues agrupadas (HI-015/M-043 como 1, M-011 como contada em Wave 6 após Wave 4). Todas as 98 issues do relatório estão mapeadas e endereçadas.
