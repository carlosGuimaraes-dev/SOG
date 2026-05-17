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

## Histórico de implementações (continuação)

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

### 2026-05-17 — Correções P3 no extrator de PDF (reviewer — ressalvas desejáveis)
- **Arquivos alterados:**
  - `agente/src/modulos/extrator_pdf.py`:
    - `resultado_base` em `extrair_texto_pdf()` agora inclui `"custas_iniciais": {"encontrado": False, "scanned": False}` — elimina inconsistência de contrato quando exceção ocorre no loop de páginas (o `return` do `except` devolvia dict sem essa chave).
    - Threshold scanned: `proporcao_scanned > 0.8` → `>= 0.8`. PDFs com exatamente 80% de páginas image-only agora são corretamente marcados como scanned.
    - Comentário explicativo adicionado acima da heurística de scanned detection documentando a racionalidade dos thresholds (0.8 e 100).
- **Testes:** 15/15 passaram. PDF real continua `scanned=False`.
