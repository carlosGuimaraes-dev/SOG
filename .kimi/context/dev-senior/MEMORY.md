# MEMORY — Dev Senior

> Arquivo dinâmico. Registre padrões locais, gotchas e débitos técnicos.

---

## Padrões de código do projeto

1. **Escaping CSS em Playwright:** Sempre usar `page.get_by_text(texto, exact=True)` como primeira estratégia. Quando necessário usar seletores CSS com `:has-text()`, escapar via `escape_for_css()` (importável de `modulos.css_escape`).
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

## Histórico de implementações (continuação)

### 2026-05-18 — Bugfix: Duplicação de `custas_pagas` no pipeline
- **Arquivo modificado:** `agente/src/pipeline.py`
  - Removido parâmetro `custas_iniciais` de `_construir_payload()`.
  - Removido bloco de mesclagem de custas iniciais de `_construir_payload()` (linhas 80-90 originais).
  - Removido argumento `custas_iniciais=custas_extraidas` da chamada de `_construir_payload` em `processar_processo()`.
  - `custas_extraidas` ainda é passada para `processar_documentos(docs, textos, custas_iniciais=custas_extraidas)` — o `parser.py` continua sendo a única fonte de mesclagem.
- **Razão:** O `parser.py` já mesclava `custas_iniciais` em `resultado["custas_pagas"]`. O `_construir_payload` mesclava novamente sobre `dados_parser.get("custas_pagas", [])`, causando duplicação.
- **Testes:** 74/74 agente passaram. Build frontend passou.

### 2026-05-18 — Fase 4: Integração de Custas Iniciais no Payload SISTJWEB
- **Arquivos modificados:**
  - `agente/src/modulos/pje.py` — adicionado método `baixar_documento_pdf(doc_id, caminho_destino)` com `@retry_on_exception`. Localiza linha do doc_id na tabela de documentos, procura links clicáveis na linha, usa `page.expect_download()` para capturar o PDF e salva em `caminho_destino`.
  - `agente/src/pipeline.py` — reestruturado fluxo de `processar_processo`:
    - `_coletar_documentos` agora retorna apenas `(docs, textos)` (parser movido para fora).
    - Após coleta, itera docs do tipo `"Comprovante de Pagamento de Custas"` ou `"Guia"`, baixa PDF temporário via `pje.baixar_documento_pdf`, extrai custas via `extrair_texto_pdf`.
    - Se `custas_iniciais["scanned"] == True`: registra log de aviso e ignora.
    - Se `custas_iniciais["encontrado"] == True`: converte para formato `{data, valor, numero_guia}` e acumula em `custas_extraidas`.
    - `processar_documentos(docs, textos, custas_iniciais=custas_extraidas)` agora recebe as custas do PDF.
    - `_construir_payload` recebe `custas_iniciais` e mescla com `dados_parser.get("custas_pagas", [])` sem duplicar por `numero_guia`.
  - `agente/src/modulos/parser.py` — `processar_documentos` agora aceita parâmetro opcional `custas_iniciais: Optional[List[Dict[str, Any]]]`. Mescla com `custas_pagas` existentes (deduplicação por `numero_guia`).
  - `agente/tests/test_parser.py` — 3 novos testes: inclusão de custas_iniciais, deduplicação por numero_guia, e entradas sem numero_guia.
- **Testes:** 74/74 agente (+3 novos), 37/37 API, build frontend passou. Sem regressões.
- **Pontos de atenção para QA:**
  - O download do PDF depende do PJe renderizar um link clicável na linha da tabela. Se o DOM mudar (ex: ícone de download em elemento não-link), o `baixar_documento_pdf` pode falhar silenciosamente (retorna False).
  - O `expect_download` requer `accept_downloads=True` no contexto do Playwright — já configurado no `AuthManager` do PJe.

### 2026-05-17 — Fase 3: Correção CR-002 (Escaping CSS em seletores)
- **Arquivos criados:**
  - `agente/src/modulos/css_escape.py` — módulo utilitário com `escape_for_css(texto: str) -> str` (escapa `\`, `'`, `"`).
  - `agente/tests/test_css_escape.py` — 6 casos de teste (string vazia, aspas simples/duplas, backslash, string comum, múltiplos especiais).
- **Arquivos modificados:**
  - `agente/src/modulos/pje.py` — `escape_for_css` removido do módulo; importado de `css_escape`. Todos os seletores dinâmicos já usavam escaping (sem regressão).
  - `agente/src/modulos/sistjweb.py` — import de `escape_for_css` migrado para `css_escape`; uso de `.format()` em `RADIO_ITEM_CALCULO` substituído por f-strings com escape explícito inline.
  - `agente/src/modulos/selectors.py` — templates com placeholders (`PJE_ETIQUETA_LINK`, `PJE_LINK_PROCESSO`, `PJE_DOC_LINK_NOME`, `RADIO_ITEM_CALCULO`) transformados em funções geradoras ou removidos. Nenhuma constante global com placeholder `{...}` restante.
- **Testes:** 71/71 passaram (6 novos em `test_css_escape.py` + 65 existentes).
- **Scan estático:** zero ocorrências de `:has-text(` + `f"` ou `.format` em seletores sem escaping em `agente/src/modulos/`.

### 2026-05-17 — Fase 1.3: Agente como Serviço Longo
- **Arquivos criados:**
  - `agente/src/servico.py` — entry point do serviço longo com máquina de estados (`parado → autenticando → executando → dormindo → ...`), graceful shutdown via `threading.Event` + signals (SIGINT/SIGTERM), heartbeat no SQLite a cada iteração, PID persistido no banco.
  - `agente/src/pipeline.py` — renomeado de `main.py`; contém toda a lógica de processamento existente (`_obter_ou_criar_processo`, `_coletar_datajud`, `_coletar_documentos`, `_construir_payload`, `_preencher_sistj`, `_notificar_erro`, `processar_processo`) + nova função `rodar_pipeline(pje, sistj)` que executa UMA iteração completa (coleta + processamento + notificação).
  - `run_agente.sh` — script wrapper executável que ativa venv, seta PYTHONPATH e executa `servico.py`.
- **Arquivos modificados:**
  - `shared/sog_shared/schema.sql` — adicionada tabela `agente_controle` (monorregistro com `CHECK (id = 1)`).
  - `shared/sog_shared/db.py` — adicionadas `obter_controle_agente()`, `criar_ou_atualizar_controle_agente()`, `listar_aprovados()`.
  - `agente/src/modulos/emissor.py` — adaptado para receber clients instanciados (`emitir_e_anexar(processo_id, sistj, pje)` e `emitir_pendentes(sistj, pje)`); elimina criação/destruição de clients a cada emissão.
  - `agente/src/banco/db.py` — wrapper atualizado para re-exportar as novas funções do `sog_shared.db`.
- **Arquivos deletados:**
  - `agente/src/main.py` — renomeado para `pipeline.py`.
  - `agente/crontab` — não é mais necessário no modelo de serviço longo.
- **Decisões:**
  - Autenticação no estado `autenticando` ainda usa `login()` programático (Fase 2 virá com `AuthManager`).
  - `_preencher_sistj` preserva `sistj.login()` interno (lógica original do `main.py`). Redundância será eliminada na Fase 2 com `garantir_autenticado()`.
  - Heartbeat atualiza `atualizado_em` e `pid` no início de cada iteração do loop via `_atualizar_heartbeat()`.
  - Sleep no estado `dormindo` usa `self._stop_event.wait(timeout=30)` para permitir interrupção imediata.
- **Testes:** 65/65 passaram. Importação de `pipeline` e `servico` verificada sem side-effects.

### 2026-05-16 — Bugfixes PDF + Extração de documentos da capa
- **Bugs corrigidos:**
  - `agente/scripts/testar_pdf.py:201` — parser agora usa `dispositivo` em vez de `texto_completo` (evita match de honorários em petições).
  - `agente/src/modulos/extrator_sentenca.py:146` — `valor.rstrip(".")` → `valor.rstrip(".,;")` (remove vírgula residual do regex).
- **Evolução:**
  - `agente/src/modulos/extrator_pdf.py` — nova função `extrair_documentos_capa()` que extrai a tabela de documentos do PJe das primeiras páginas do PDF. Heurística: state machine por linhas, separação nome/tipo via lista de tipos conhecidos. Retorna `[]` em caso de falha (nunca quebra).
  - Campo `documentos_capa` adicionado ao dict retornado por `extrair_texto_pdf()` — contrato preservado, campo novo apenas.
  - `agente/scripts/testar_pdf.py` — exibe tabela de documentos da capa no output (rich + ANSI fallback).
  - `agente/tests/test_extrator_pdf.py` — teste `test_extrair_documentos_capa` valida extração do PDF real (120 docs, tipos como Mandado/Diligência/Comprovante de Pagamento de Custas identificados).
- **Testes:** 57/57 agente + 30/30 API passaram.

### 2026-05-16 — Função utilitária `mapear_tipo_sistjweb`
- **`agente/src/modulos/extrator_pdf.py`** — adicionada função `mapear_tipo_sistjweb(tipo_pje: str) -> str` que mapeia tipos de documento do PJe para os campos do payload SISTJWEB:
  - Mandado → `ids_mandados`
  - Ofício → `ids_oficios`
  - Alvará → `ids_alvaras`
  - Traslado → `ids_traslados`
  - Carta de Sentença → `ids_cartas_sentenca`
  - AR → `ids_ar`
  - AR/MP → `ids_armp`
  - Diligência → `ids_circunscricao_origem`
  - Comprovante de Pagamento de Custas → `custas_pagas`
  - Tipos não mapeados retornam `""`.
- **Nota:** A função `extrair_documentos_capa()` e o campo `documentos_capa` no retorno de `extrair_texto_pdf()` já existiam no arquivo (implementados na sessão anterior). A adição desta sessão foi apenas `mapear_tipo_sistjweb`.

### 2026-05-16 — Script CLI de teste de PDFs judiciais
- **Arquivo modificado:** `agente/scripts/testar_pdf.py` — ajustado para seguir especificação exata:
  - `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))` no topo
  - Fallback ANSI colors quando `rich` não está instalado (cores para sucesso/erro/aviso)
  - `try/except` generoso no `main()` capturando falhas de extração e parsing
  - Aviso de PDF scanned em vermelho (`\033[31m`)
  - Saída JSON indentada com `--verbose`
- **Arquivos já existentes (não modificados):** `agente/tests/test_extrator_pdf.py` (já atendia requisitos), `agente/requirements.txt` (já tinha `pymupdf==1.24.5`).

---

## Débitos técnicos identificados (fora do escopo)

1. ~~**`agente/src/modulos/selectors.py`** contém templates com placeholders CSS inseguros.~~ Resolvido na Fase 3 (CR-002). Templates transformados em funções geradoras com escaping via `css_escape.py`.
2. **`agente/src/modulos/extrator_sentenca.py:277`** — o `except Exception` fallback do LLM ainda silencia erros da API OpenAI sem log. O plano não exigiu alteração aqui, mas para debug futuro pode ser útil adicionar `erro()`.
3. **`agente/src/modulos/retry.py`** — os `except Exception: pass` em `is_session_expired` (linhas 82, 86, 103) são intencionalmente resilientes, mas poderiam logar em nível DEBUG.
4. **`api/src/rotas/processos.py`** — `SCREENSHOTS_BASE_DIR` é hardcoded para `/dados/screenshots`. Na Wave 8 (PostgreSQL) ou quando mudar volumes, extrair para variável de ambiente `SCREENSHOTS_DIR`.
5. **`api/tests/test_api.py`** — O teste de concorrência (`test_aprovar_race_condition_apenas_uma_aprovacao`) não simula verdadeira concorrência porque `:memory:` não é compartilhável entre threads de forma segura. Para teste de carga real, usar arquivo `.db` temporário com múltiplos TestClient em threads.
9. **Isolamento de testes API + Agente:** Quando `pytest api/tests/ agente/tests/` é executado em uma única invocação, os testes `test_iniciar_agente` e `test_parar_agente` falham com `no such table: agente_controle`. Rodados isoladamente (`pytest api/tests/` e `pytest agente/tests/` separadamente), ambos passam 100%. Possível causa: conflito de monkeypatch entre os dois `conftest.py` ou cache de schema SQL. Não é regressão da Fase 2.
6. **`agente/src/config.py` vs `shared/sog_shared/config.py`:** Duplicação sutil de `DB_PATH`, `TIMEOUT_PADRAO`, `HEADLESS`, `MAX_TENTATIVAS`. O agente ainda mantém seu próprio `config.py` com todas as variáveis (incluindo específicas como PJE/SISTJ/SMTP/LLM). A longo prazo, migrar o agente para importar as variáveis comuns do `sog_shared.config` eliminaria a duplicação.
7. ~~**`agente/src/servico.py` — autenticação programática:** Resolvido na Fase 2. `_autenticar_todos()` agora usa `garantir_autenticado()` via `AuthManager`.~~
8. ~~**`agente/src/pipeline.py` — `_preencher_sistj` chama `sistj.login()` internamente:** Resolvido na Fase 2. `login()` agora é alias para `garantir_autenticado()`, que é no-op se a sessão já estiver viva.~~

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

### 2026-05-16 — Ponte PDF: extrator + script CLI + testes
- **Arquivos criados:**
  - `agente/src/modulos/extrator_pdf.py` — extrai texto de PDF local com PyMuPDF; isola DISPOSITIVO via heurística de coordenadas (descarta cabeçalho/rodapé) + regex; detecta PDFs scanned.
  - `agente/scripts/testar_pdf.py` — CLI que recebe caminho de PDF, extrai texto, envia para `extrair_sentenca` e `processar_documentos`, imprime resumo colorido (rich) e JSON.
  - `agente/tests/test_extrator_pdf.py` — testes unitários: PDF real, scanned mock, arquivo inexistente, heurística de dispositivo.
- **Arquivos alterados:**
  - `agente/requirements.txt` — adicionado `pymupdf==1.24.5`.
- **Heurística DISPOSITIVO:**
  - Busca por `DISPOSITIVO` e `ANTE O EXPOSTO` com terminadores (`Assinado`, `LOCAL E DATA`, `Intimem-se`).
  - Prioriza match que contenha `"condeno"` (evita falsos positivos de petições/razões de recurso).
  - Fallback: últimos 25% do texto.
- **Scanned detection:** por página, se `len(texto_bruto.strip()) < 30` e `page.get_images()` não vazio.
- **Desvio do plano (sinalizado):** O regex `DISPOSITIVO` isolado capturava "Dispositivo de iluminação diurna" de documentos de seguro no PDF real (falso positivo). Foi necessário adicionar priorização por `"condeno"` nos matches para garantir que o dispositivo da sentença seja isolado corretamente.
- **Testes:** 56/56 passaram (6 novos em `test_extrator_pdf.py` + 50 existentes). PDF real extrai corretamente: sucumbente=MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA, valor=10.158,00, honorários=10%, suspensão=Sim, score=1.00, método=regex.

### 2026-05-17 — Extração de valor das custas iniciais de PDF
- **Arquivos alterados:**
  - `agente/src/modulos/extrator_pdf.py` — adicionadas funções `_parse_valor_monetario()`, `_extrair_valor_guia()`, `extrair_custas_iniciais()`. Regex específicos ao TJDFT para valor total, detalhamento por item (Distribuidor, Mandados, Ofícios, Contador, Custas, Diligências), número da guia e vencimento. Campo `"custas_iniciais"` adicionado ao dict retornado por `extrair_texto_pdf()` — sem dupla abertura de PDF (reuso de dados já extraídos).
  - `agente/tests/test_extrator_pdf.py` — 7 novos testes: PDF real (valor_total="266,95", detalhamento com 6/6 itens, numero_guia="001-9"), guia sem detalhamento (mock), sem guia (mock), scanned (mock), `extrair_texto_pdf` inclui campo, e utilitário `_parse_valor_monetario`.
  - `agente/scripts/testar_pdf.py` — exibe `Custas Iniciais` na tabela rich e saída ANSI; inclui JSON de custas na saída.
- **Gotcha identificado:** O cabeçalho `Num. {doc_id} - Pág. N` da página da guia é descartado pelo filtro de coordenadas de `extrair_texto_pdf()` (cabeçalho/rodapé). Isso impede a localização da guia pelo `doc_id` no texto filtrado. Solução: fallback que busca por `"Guia de Custas e Emolumentos"` no texto quando o doc_id não produz match.
- **Gotcha identificado:** Em formulários de guia do TJDFT, o rótulo "Vencimento" pode aparecer fisicamente abaixo da data no PDF, causando inversão na extração de texto (`11/08/2024` vem antes de `Vencimento`). Solução: fallback de vencimento que busca datas em janela de ±200 chars ao redor de qualquer ocorrência de "Vencimento".
- **Testes:** 13/13 passaram em `test_extrator_pdf.py` (6 originais + 7 novos).

### 2026-05-17 — Correções P2/P3 na extração de custas iniciais (review)
- **Arquivos alterados:**
  - `agente/src/modulos/extrator_pdf.py`:
    - `_parse_valor_monetario()` — substituído parsing via `float` por aritmética inteira (remove imprecisão decimal em valores monetários). Separa na vírgula em `inteiros * 100 + centavos`.
    - `_extrair_valor_guia()` — `valor_total` agora é extraído do regex explícito `"Valor total"` primeiro; soma do detalhamento é usada apenas como fallback quando o regex falha.
    - `extrair_custas_iniciais()` — fallback estratégia 2 (busca por `"Guia de Custas e Emolumentos"`) agora cobre também `"comprovante de pagamento de custas"`.
    - Typo corrigido: `_JANELA_GUIA_EXPandida` → `_JANELA_GUIA_EXPANDIDA`.
    - Dead code removido: `encontrado = False` (linha 498).
  - `agente/tests/test_extrator_pdf.py` — teste renomeado: `test_extrair_custas_iniciais_guia_sem_detalhamento` → `test_extrair_valor_guia_sem_detalhamento`.
- **Testes:** 13/13 passaram. PDF real continua retornando `valor_total="266,95"`.

### 2026-05-17 — Correções P2 no extrator de PDF (double-close + falso positivo scanned)
- **Arquivos alterados:**
  - `agente/src/modulos/extrator_pdf.py`:
    - Removido `doc.close()` do bloco `except` de `extrair_texto_pdf()` (linha 629). O recurso agora é liberado exclusivamente no `finally`, eliminando double-close em exceção.
    - Heurística de scanned detection reescrita: de "qualquer página image-only marca tudo" para agregada — `proporcao_scanned > 0.8 and media_texto < 100`. Isso elimina falsos positivos em PDFs cuja capa tenha brasão/imagem com poucas palavras, mas cujo corpo seja texto selecionável.
    - Variáveis `paginas_scanned` e `total_texto_bruto` acumuladas durante o loop; cálculo aplicado após o loop com guarda `num_paginas > 0`.
  - `agente/tests/test_extrator_pdf.py`:
    - Teste `test_detectar_scanned_pdf` — verificado, continua passando (2/2 páginas scanned, 100% > 0.8, média 1 < 100).
    - Novo `test_nao_marcar_scanned_capa_imagem` — 5 páginas (1 image-only + 4 texto extenso), verifica `scanned=False`.
    - Novo `test_double_close_nao_ocorre` — mock que lança exceção no loop, verifica `doc.close.assert_called_once()`.
- **Testes:** 15/15 passaram (13 originais + 2 novos). PDF real continua `scanned=False`.

### 2026-05-18 — Fase 2: AuthManager + Storage State + Fallback Interativo
- **Arquivos criados:**
  - `agente/src/modulos/auth_manager.py` — `AuthManager` com storage state Playwright (`context.storage_state()`) e fallback interativo (`headless=False`, polling a cada 2s, timeout 10min). Classe `ReautenticacaoNecessariaError(Exception)` com atributo `sistema`.
- **Arquivos modificados:**
  - `agente/src/config.py` — adicionados `STORAGE_STATE_DIR`, `STORAGE_STATE_PJE`, `STORAGE_STATE_SISTJ` (default `~/.sog/auth/`).
  - `agente/src/modulos/playwright_client.py` — removida inicialização direta de browser; `page`/`browser` agora são properties delegando para `self._auth`; `fechar()` delega para `self._auth.fechar()`.
  - `agente/src/modulos/pje.py` — `PjeClient.__init__` instancia `AuthManager(STORAGE_STATE_PJE)`; `garantir_autenticado()` chama `verificar_e_autenticar()`; `login()` é alias para `garantir_autenticado()`; lógica de verificação de login extraída para `_esta_logado(page)`.
  - `agente/src/modulos/sistjweb.py` — `SistjClient.__init__` instancia `AuthManager(STORAGE_STATE_SISTJ)`; `garantir_autenticado()` + `_esta_logado(page)` + `login()` alias; removido login programático.
  - `agente/src/modulos/retry.py` — na seção de reconexão: se `instance._auth` existe, lança `ReautenticacaoNecessariaError` em vez de tentar reconexão programática; comportamento legado preservado quando `_auth` não existe.
  - `agente/src/modulos/emissor.py` — `sistj.login()`/`pje.login()` trocados por `garantir_autenticado()`.
  - `agente/src/servico.py` — `_autenticar_todos()` chama `garantir_autenticado()`; adicionado `_autenticar_interativo()`; estados `autenticando` e `executando` capturam `ReautenticacaoNecessariaError` e transicionam para `aguardando_login`; estado `aguardando_login` chama `_autenticar_interativo()` e trata `TimeoutError`.
- **Decisões:**
  - Login programático (usuário/senha hardcoded no `.env`) foi completamente removido do fluxo ativo. As variáveis `PJE_USUARIO`/`PJE_SENHA`/`SISTJ_USUARIO`/`SISTJ_SENHA` ainda existem no `config.py` para compatibilidade, mas não são mais usadas.
  - O `_esta_logado` do SISTJWEB usa heurística combinada: ausência de campos de login + presença de menu/elementos logados + URL sem "login".
  - O `_esta_logado` do PJe reutiliza a mesma lógica de verificação que existia no `login()` original (indicadores via env + seletores genéricos + verificação de URL).
- **Testes:** 37/37 API, 124/124 frontend, 65/65 agente. Todos passaram.

### 2026-05-18 — Fase 1.1: Backend API — Controle do agente via SQLite
- **Arquivos criados:**
  - `api/src/rotas/agente.py` — endpoints `POST /agente/iniciar`, `POST /agente/parar`, `GET /agente/status`
- **Arquivos modificados:**
  - `shared/sog_shared/schema.sql` — tabela `agente_controle` com `CHECK (id = 1)` (monorregistro)
  - `agente/src/banco/schema.sql` — espelho do shared para testes
  - `shared/sog_shared/db.py` — funções `obter_controle_agente()`, `criar_ou_atualizar_controle_agente()`, `listar_aprovados()`
  - `api/src/schemas.py` — `AgenteStatusResponse`, `AgenteComandoResponse`
  - `api/src/app.py` — registro do router `agente`
  - `api/src/rotas/__init__.py` — export de `agente`
  - `api/src/rotas/aprovacao.py` — removido `BackgroundTasks` e `_disparar_emissao`; mensagem alterada para "O agente processará a emissão em breve."
  - `api/tests/test_api.py` — 6 novos testes para endpoints do agente; mensagem de aprovação atualizada
- **Decisões:**
  - Campo `online` calculado comparando `atualizado_em` (assumido UTC, pois SQLite retorna naive) com `datetime.now(timezone.utc)`. Sem essa correção, `datetime.now()` local (UTC-7) daria falso positivo de online.
  - Rate limiting de 10/minute aplicado em todos os 3 endpoints do agente.
  - A API NUNCA executa o agente (sem subprocess); apenas grava `comando` na tabela.
- **Testes:** 37/37 passaram em 1.30s.

### 2026-05-17 — Correção de duplicações em shared/sog_shared/schema.sql e db.py
- **Problema 1:** `shared/sog_shared/schema.sql` continha a tabela `agente_controle` duplicada (linhas 79-86 e 88-95). Segunda cópia removida.
- **Problema 2:** `shared/sog_shared/db.py` continha as funções `obter_controle_agente`, `criar_ou_atualizar_controle_agente` e `listar_aprovados` duplicadas (linhas 238-296 e 298-355). Segunda cópia removida.
- **Verificação:** grep confirmou exatamente 1 ocorrência restante de cada entidade duplicada.

### 2026-05-18 — Correções P2 do code review (Fase 1)
- **Arquivos alterados:**
  - `agente/src/servico.py` — removido import `from banco import db`; padronizado para importar `init_db`, `obter_controle_agente`, `criar_ou_atualizar_controle_agente` exclusivamente de `sog_shared.db`. Corrigida f-string esquecida na linha 84 (`PID={os.getpid()}` → `f"PID={os.getpid()}"`).
  - `shared/sog_shared/db.py` — `criar_ou_atualizar_controle_agente()` agora executa `BEGIN IMMEDIATE` no início da transação, `conn.commit()` no sucesso e `conn.rollback()` em caso de exceção, eliminando race condition quando API e agente escrevem simultaneamente no monorregistro.
  - `api/src/rotas/aprovacao.py` — endpoint `/rejeitar/{id}` agora valida que o processo está em status `aguardando_aprovacao` antes de rejeitar, retornando HTTP 400 caso contrário (paridade com `/aprovar/{id}`).
- **Decisão:** `agente/src/banco/db.py` (wrapper de 21 linhas) foi mantido pois `main.py`, `modulos/emissor.py` e `modulos/pje.py` ainda o utilizam. Apenas `servico.py` foi padronizado.
- **Testes:** API 37/37 passaram em 1.26s. Frontend 124/124 passaram em 12.85s.

### 2026-05-17 — Correções P3 no extrator de PDF (reviewer — ressalvas desejáveis)
- **Arquivos alterados:**
  - `agente/src/modulos/extrator_pdf.py`:
    - `resultado_base` em `extrair_texto_pdf()` agora inclui `"custas_iniciais": {"encontrado": False, "scanned": False}` — elimina inconsistência de contrato quando exceção ocorre no loop de páginas (o `return` do `except` devolvia dict sem essa chave).
    - Threshold scanned: `proporcao_scanned > 0.8` → `>= 0.8`. PDFs com exatamente 80% de páginas image-only agora são corretamente marcados como scanned.
    - Comentário explicativo adicionado acima da heurística de scanned detection documentando a racionalidade dos thresholds (0.8 e 100).
- **Testes:** 15/15 passaram. PDF real continua `scanned=False`.
