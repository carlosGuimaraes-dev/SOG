# MEMORY — Dev Senior

> Arquivo dinâmico. Registre padrões locais, gotchas e débitos técnicos.

---

## Padrões de código do projeto

1. **Escaping CSS em Playwright:** Sempre usar `page.get_by_text(texto, exact=True)` como primeira estratégia. Quando necessário usar seletores CSS com `:has-text()`, escapar via `escape_for_css()` (importável de `modulos.pje`).
2. **Retry:** O decorator `@retry_on_exception` tem default `(PlaywrightTimeout, ConnectionError, TimeoutError)`. Nunca usar `(Exception,)` como default.
3. **PII em logs:** Nunca logar dicts completos de dados de processo. Logar apenas `processo_id`, `etapa`, `status`, e contagens (`len(dados)`, `campos=N`).
4. **HTML em emails:** Sempre usar `html.escape()` em valores interpolados em templates HTML.
5. **Datetime UTC:** Usar `datetime.now(timezone.utc)` — `datetime.utcnow()` foi removido do codebase.
6. **Cookies httpOnly em erro 401:** `HTTPException` não propaga `Set-Cookie`. Quando precisar limpar cookies em respostas de erro, usar `JSONResponse` diretamente e chamar `.set_cookie()` nele, não no `Response` injetado.
7. **Path traversal em FileResponse:** Sempre resolver o path absoluto e verificar `.relative_to(diretorio_base)` antes de servir arquivos do filesystem.
8. **SQLite em testes:** Usar `sqlite3.connect(":memory:", check_same_thread=False)` ao mockar `db.get_conn()` para TestClient (FastAPI roda requests em threads).
9. **BEGIN IMMEDIATE para race conditions:** Em operações críticas (aprovação/rejeição), sempre usar `BEGIN IMMEDIATE` dentro de uma única conexão e nunca chamar funções que abrem conexões separadas.
10. **Response models Pydantic:** Todo endpoint deve declarar `response_model=` no decorator. Nunca expor `Dict[str, Any]` ou `List[Dict[str, Any]]` diretamente.
11. **Rate limiting com slowapi:** Usar `limiter = Limiter(key_func=get_remote_address)` compartilhado via `api/src/limiter.py`. Decorar endpoints com `@limiter.limit("N/minute")`. Adicionar `request: Request` aos parâmetros da função.
12. **Pacote shared/:** `sog_shared.db`, `sog_shared.schemas` e `sog_shared.config` são a fonte única de verdade para código compartilhado entre API e Agente. Nunca usar `sys.path.insert` para importar código de outro serviço.
13. **PlaywrightClient base:** `PjeClient` e `SistjClient` herdam de `modulos.playwright_client.PlaywrightClient`. Atributos comuns (browser, page, viewport, headless, timeout) ficam na classe base.

---

## Gotchas e pegadinhas

1. **Playwright `text='...'` é vulnerável a injeção CSS** quando o texto contém apóstrofos ou aspas (ex: "D'AVILA"). A função `escape_for_css()` trata isso, mas preferir `get_by_text` sempre que possível.
2. **Regex com quantificadores `.+?` em textos judiciais longos** pode causar backtracking catastrófico. Usar bounds (`{1,200}`) ou classes negadas (`[^.]{0,100}`).
3. **JSONDecodeError no LLM:** A resposta da OpenAI pode ser malformada. Sempre envolver `json.loads` em `try/except json.JSONDecodeError` com log do conteúdo truncado.
4. **Slice mágico em número CNJ:** Validar `len(numero) == 20` e `numero.isdigit()` antes de `numero[14:16]`.
5. **python-jose `jwt.decode` com `aud` claim:** Se o token contém `aud`, o `decode` exige `audience=` explicitamente, senão lança `JWTError: Invalid audience`. Sempre passar `audience=` e `issuer=` quando essas claims estiverem presentes.
6. **TestClient e cookies:** `client.cookies.set()` sem `domain` cria cookies com domain vazio, que podem causar `CookieConflict` quando o servidor responde com cookies do mesmo nome. Sempre usar `domain="testserver.local", path="/"` em testes que manipulam cookies manualmente.
7. **slowapi com TestClient:** O limiter do slowapi requer `request: Request` nos parâmetros do endpoint para identificar o client. Sem isso, pode lançar `AttributeError`.
8. **SQLite WAL em :memory::** `PRAGMA journal_mode=WAL` é aceito mas sem efeito prático em `:memory:`. Para testes de concorrência real, usar arquivo compartilhado.
9. **sog_shared em testes locais:** Os `conftest.py` adicionam `shared/` ao `sys.path` para que `import sog_shared` funcione sem `pip install -e`. Nos containers, o `pip install -e ./shared` no Dockerfile garante disponibilidade.

---

## Débitos técnicos identificados (fora do escopo)

1. **`agente/src/modulos/selectors.py`** contém templates com placeholders CSS inseguros (`text='{etiqueta}'`, `text='{numero}'`, `text='{nome}'`). Essas constantes não são usadas no código atual (código morto), mas representam risco se forem reativadas. Recomendação: remover na Wave 7 ou 8.
2. **`agente/src/modulos/extrator_sentenca.py:277`** — o `except Exception` fallback do LLM ainda silencia erros da API OpenAI sem log. O plano não exigiu alteração aqui, mas para debug futuro pode ser útil adicionar `erro()`.
3. **`agente/src/modulos/retry.py`** — os `except Exception: pass` em `is_session_expired` (linhas 82, 86, 103) são intencionalmente resilientes, mas poderiam logar em nível DEBUG.
4. **`api/src/rotas/processos.py`** — `SCREENSHOTS_BASE_DIR` é hardcoded para `/dados/screenshots`. Na Wave 8 (PostgreSQL) ou quando mudar volumes, extrair para variável de ambiente `SCREENSHOTS_DIR`.
5. **`api/tests/test_api.py`** — O teste de concorrência (`test_aprovar_race_condition_apenas_uma_aprovacao`) não simula verdadeira concorrência porque `:memory:` não é compartilhável entre threads de forma segura. Para teste de carga real, usar arquivo `.db` temporário com múltiplos TestClient em threads.
6. **`agente/src/config.py` vs `shared/sog_shared/config.py`:** Duplicação sutil de `DB_PATH`, `TIMEOUT_PADRAO`, `HEADLESS`, `MAX_TENTATIVAS`. O agente ainda mantém seu próprio `config.py` com todas as variáveis (incluindo específicas como PJE/SISTJ/SMTP/LLM). A longo prazo, migrar o agente para importar as variáveis comuns do `sog_shared.config` eliminaria a duplicação.

---

## Histórico de implementações

### 2026-05-15 — Wave 2: Segurança Crítica II (Agente + Playwright + Dados)
- **15 issues corrigidas** em `agente/src/`.
- Arquivos alterados: `main.py`, `modulos/pje.py`, `modulos/sistjweb.py`, `modulos/retry.py`, `modulos/datajud.py`, `modulos/extrator_sentenca.py`, `utils/logger.py`, `utils/notificador.py`, `regras.py`, `banco/db.py`, `tests/test_extrator_sentenca.py`.
- **Testes:** 50/50 passaram. Regex < 100ms para 50KB verificado. Retry com NameError não dispara. HTML escaping verificado.

### 2026-05-15 — Wave 3: Auth Cross-Cutting (Backend)
- **5 issues corrigidas** no backend.
- Arquivos alterados:
  - `api/src/auth.py` — claims `iss`/`aud`/`iat` nos tokens; `get_current_user` lê cookie `access_token` com fallback para `Authorization` header.
  - `api/src/rotas/auth.py` — login/refresh emitem `httpOnly Secure SameSite=Strict` cookies; refresh lê cookie; refresh inválido retorna 401 e limpa cookies via `JSONResponse`.
  - `api/src/rotas/processos.py` — novo endpoint `GET /processos/{id}/screenshot` com autenticação, path traversal protection, `FileResponse(image/png)` e `Cache-Control: private, max-age=300`.
  - `api/src/app.py` — `root_path="/api/v1"` para versionamento de API.
  - `nginx/nginx.conf` e `nginx/nginx-dev.conf` — `location /api/v1/` com `proxy_pass http://api:8000/api/v1/`.
  - `agente/src/banco/db.py` — type hint `processo_existe` corrigido para `Optional[Dict[str, Any]]`.
  - `api/tests/test_api.py` — testes atualizados para contrato cookie + `/api/v1/`.
- **Testes:** 19/19 passaram. Cookie httOnly verificado. Path traversal retorna 400. Refresh reutilizado retorna 401 com cookies limpos.

### 2026-05-15 — Wave 3 (continuação): Endpoints /auth/me e /auth/logout
- **2 endpoints adicionados** em `api/src/rotas/auth.py`:
  - `GET /auth/me` — usa `get_current_user` como dependency (cookie `access_token` com fallback para `Authorization: Bearer`). Retorna `{"username": ...}` ou 401.
  - `POST /auth/logout` — lê cookie `refresh_token`, decodifica, revoga JTI se válido, sempre retorna 200 e limpa ambos os cookies via `_clear_auth_cookies` (idempotente).
- Arquivos alterados:
  - `api/src/rotas/auth.py` — adicionados imports `Depends`, `get_current_user`; endpoints `/me` e `/logout`.
  - `api/tests/test_api.py` — 5 novos testes: `test_me_com_cookie_valido`, `test_me_sem_cookie`, `test_me_com_header_valido`, `test_logout_com_refresh_valido` (inclui verificação de revogação via reuse em `/refresh`), `test_logout_sem_cookie`.
- **Testes:** 24/24 passaram.

### 2026-05-15 — Wave 4: Backend API — Concorrência, Paginação, Models
- **12 issues corrigidas** no backend + agente.
- Arquivos alterados:
  - `api/src/schemas.py` — **novo** — schemas Pydantic: `ProcessoResponse`, `ProcessoListResponse`, `ProcessoDetalheResponse`, `AprovacaoResponse`, `RejeicaoResponse`, `HistoricoItemResponse`, `LoginResponse`, `TokenRefreshResponse`, `LogoutResponse`, `MeResponse`, `HealthResponse`.
  - `api/src/limiter.py` — **novo** — `Limiter` compartilhado do slowapi.
  - `api/src/rotas/aprovacao.py` — `BEGIN IMMEDIATE` em transação única para aprovação/rejeição; `threading.Thread` substituído por `BackgroundTasks`; rate limit `10/minute`.
  - `api/src/rotas/processos.py` — paginação `limit`/`offset` com bounds (`ge=1, le=1000`); `detalhar_processo` refatorado para JOIN único em uma única conexão; rate limit `30/minute`.
  - `api/src/rotas/historico.py` — paginação com `Query` bounds; rate limit `30/minute`.
  - `api/src/rotas/auth.py` — rate limit `5/minute` no login; todos os endpoints com `response_model`.
  - `api/src/app.py` — slowapi integrado (`_rate_limit_exceeded_handler`); lifespan chama `init_config()` e `db.init_db()`; health check com `response_model=HealthResponse`.
  - `agente/src/banco/db.py` — `_init_db()` removido do nível do módulo; `init_db()` explícita criada; `get_conn()` aplica `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000`; funções de listagem aceitam `limit`/`offset`.
  - `agente/src/config.py` — `load_dotenv()` e criação de diretórios movidos para `init_config()`; import puro não tem side-effects.
  - `agente/src/main.py` — chama `init_config()` e `db.init_db()` no startup; TODO-WAVE6 adicionado.
  - `api/src/auth.py`, `api/src/banco/db.py`, `api/src/rotas/*.py` — TODO-WAVE6 adicionado aos `sys.path.insert`.
  - `api/tests/test_api.py` — completamente refatorado para usar SQLite `:memory:` via fixture `mock_db` (`check_same_thread=False`); testes não dependem de arquivo `.db`; 28 testes.
- **Dependências instaladas:** `slowapi==0.1.9`.
- **Testes:** 28/28 passaram em 1.67s. Nenhuma dependência de arquivo `.db` no filesystem.

### 2026-05-15 — Revisão P1: HSTS nginx + wrapper agente/db.py
- **Ressalva 1 (HSTS em HTTP):** Removido `add_header Strict-Transport-Security` do bloco `server { listen 80; }` em `nginx/nginx.conf` e `nginx/nginx-dev.conf`. RFC 6797 proíbe HSTS em transporte não-seguro. Header mantido comentado para ativação futura no bloco HTTPS.
- **Ressalva 2 (agente db.py duplicado):** `agente/src/banco/db.py` convertido de 231 linhas para wrapper de 18 linhas que re-exporta de `sog_shared.db`. Todos os imports existentes em `main.py`, `modulos/emissor.py`, `modulos/pje.py` preservados.
- **Testes:** Agente 50/50 passaram. API 28/28 passaram.

### 2026-05-15 — Wave 6: Arquitetura Python — Pacote Compartilhado + SRP
- **10 issues corrigidas** (CR-008, M-011, M-010, HI-006, M-009, M-046, M-047, M-048, M-049, M-051).
- Arquivos criados:
  - `shared/pyproject.toml` — pacote `sog-shared` instalável via `pip install -e`.
  - `shared/sog_shared/__init__.py`
  - `shared/sog_shared/db.py` — cópia limpa do banco SQLite (sem side-effects no import).
  - `shared/sog_shared/schemas.py` — schemas Pydantic compartilhados.
  - `shared/sog_shared/config.py` — variáveis de ambiente comuns (DB_PATH, TIMEOUT_PADRAO, DASHBOARD_SENHA_HASH, etc.).
  - `shared/sog_shared/schema.sql` — schema SQLite.
  - `agente/src/modulos/playwright_client.py` — classe base `PlaywrightClient` com `iniciar()`, `fechar()`, `verificar_sessao()`, `reconectar()`.
- Arquivos alterados:
  - `api/Dockerfile` — removido `COPY agente/src/ ./agente_src/`; adicionado `COPY shared/ ./shared/` + `pip install -e ./shared`.
  - `agente/Dockerfile` — adicionado `COPY shared/ ./shared/` + `pip install -e ./shared`; `rm -rf /var/lib/apt/lists/*` já existia (M-051 já estava OK).
  - `api/src/app.py`, `api/src/auth.py`, `api/src/rotas/aprovacao.py`, `api/src/rotas/processos.py`, `api/src/rotas/historico.py` — removido `sys.path.insert`; imports migrados para `sog_shared`.
  - `api/src/banco/db.py` — simplificado para re-exportar de `sog_shared.db`.
  - `agente/src/main.py` — removido `sys.path.insert`; `processar_processo` refatorado de 96 para 26 linhas; extraídas `_obter_ou_criar_processo`, `_coletar_datajud`, `_coletar_documentos`, `_construir_payload`, `_preencher_sistj`, `_notificar_erro`.
  - `agente/src/modulos/pje.py`, `agente/src/modulos/sistjweb.py` — `PjeClient` e `SistjClient` agora herdam de `PlaywrightClient`; removida duplicação de inicialização.
  - `agente/src/modulos/parser.py` — `parse_sentenca` e `parse_comprovante_pagamento` agora são wrappers depreciados que reexportam de `extrator_sentenca.py`; `processar_documentos` permanece como orquestração.
  - `agente/src/modulos/extrator_sentenca.py` — adicionada `parse_comprovante_pagamento()` para eliminar duplicação.
  - `docker-compose.yml` — adicionado serviço `backup` (sidecar) que roda `sqlite3 ... .backup` a cada 24h com rotação de 7 dias.
  - `docker-compose.dev.yml` — adicionado serviço `agente`; nginx dev mapeado para `8080:80`.
  - `frontend/nginx-default.conf` — removido bloco `location /api/` duplicado.
  - `api/tests/conftest.py`, `agente/tests/conftest.py` — adicionado `shared/` ao `sys.path` para importar `sog_shared` sem instalação.
  - `api/tests/test_api.py` — monkeypatch atualizado de `"banco.db.*"` para `"sog_shared.db.*"`.
- **Testes:** API 28/28 passaram em 4.15s. Agente 50/50 passaram em 0.88s. Nenhum `sys.path.insert` restante em `api/src/` ou `agente/src/`.
