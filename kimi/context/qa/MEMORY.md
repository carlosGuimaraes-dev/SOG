# MEMORY — QA Engineer

> Arquivo dinâmico. Registre configuração do ambiente de testes, padrões
> de bugs recorrentes e áreas de risco mapeadas no projeto.

---

## Configuração do ambiente de testes

- Comando: `pytest agente/tests/ -v`
- Comando API: `cd api && pytest tests/ -v`
- Requer: Python 3.12+, variáveis `JWT_SECRET_KEY` e `FRONTEND_URL` exportadas para testar API
- Banco: SQLite compartilhado entre agente e API (próximas waves migram para PostgreSQL)

---

## Padrões de bugs recorrentes

- Variáveis de ambiente críticas (`JWT_SECRET_KEY`, `FRONTEND_URL`) ausentes em `.env.api` causam falha no startup da API.
- `.env.api` deve ser verificado sempre que `auth.py` ou `app.py` forem alterados.
- Frontend consome endpoints `/auth/me` e `/auth/logout` que precisam existir no backend para auth cross-cutting funcional.

---

## Áreas de risco identificadas

- Autenticação JWT: validação no import (eager) — qualquer env var faltante quebra o app antes do lifespan.
- Playwright CSS injection: função `escape_for_css` adicionada, mas fallback CSS ainda usado em muitos lugares; manter monitoramento.
- Regex de sentença: bounds adicionados, mas sem teste de performance com textos > 50KB.
- Refresh token reuse: backend implementa revogação, mas endpoint `/auth/logout` ausente — cookies não são limpos no logout.

---

## Histórico de validações

- 2026-05-15: Waves 1 e 2 (Infra + Backend + Agente) — REPROVADO
  - Bug #1: `.env.api` incompleto (falta `JWT_SECRET_KEY` e `FRONTEND_URL`) — BLOQUEADOR
  - Demais critérios: todos APROVADOS
  - Testes automatizados: 25/25 passaram

- 2026-05-15: Wave 3 (Auth Cross-Cutting) — REPROVADO
  - Todos os critérios explícitos de aceite: APROVADOS
  - Bug #1: Endpoints `/auth/me` e `/auth/logout` ausentes no backend — ALTO
  - Testes automatizados: 19/19 passaram (API), 50/50 passaram (Agente)

- 2026-05-15: Wave 3 (Auth Cross-Cutting) — CORREÇÃO PONTUAL VALIDADA — APROVADO
  - Endpoints `/auth/me` e `/auth/logout` implementados em `api/src/rotas/auth.py`
  - Testes correspondentes adicionados em `api/tests/test_api.py`
  - Resultado: 24/24 passaram (API)
  - Warnings: 15 preexistentes (deprecation passlib/jose), nenhum novo

- 2026-05-15: Wave 4 (Backend API: Concorrência, Paginação, Models) — APROVADO
  - Todos os critérios explícitos de aceite: APROVADOS
  - Testes automatizados: 28/28 passaram (API) em 2.08s
  - Warnings: 18 preexistentes (deprecation passlib/jose), nenhum novo
  - Side-effects no import: validado — `import config` em diretório limpo não cria diretórios
  - sys.path.insert: todos os arquivos têm comentário `# TODO-WAVE6`

- 2026-05-15: Wave 5 (Frontend: Refatoração, UX e Testes) — APROVADO
  - Todos os critérios explícitos de aceite: APROVADOS
  - Testes automatizados: 12/12 passaram (Login, Fila, Detalhe)
  - Cobertura de testes: 66.17% statements, 64.28% branches, 65.85% funcs, 66.17% lines
  - Build passou sem erros TypeScript; chunks lazy separados gerados (Detalhe 9.70 kB, Historico 2.06 kB)
  - Warnings: React Router future flags preexistentes nos testes (não bloqueantes)

- 2026-05-15: Wave 7 (Infra Hardening Completo) — REPROVADO
  - Agente Dockerfile: todos os critérios APROVADOS
  - Frontend Dockerfile: APROVADO
  - Requirements split (txt vs dev): APROVADO
  - Nginx (prod e dev): todos os critérios APROVADOS
  - Docker Compose dev: todos os critérios APROVADOS
  - Bug #1: docker-compose.yml serviço `backup` sem `security_opt`, `cap_drop` e resource limits — MÉDIO
  - Bug #2: `.gitignore` não cobre padrão `.env*` nem diretório `dados/` — MÉDIO
  - Observação: serviço `agente` no docker-compose.yml não está conectado a nenhuma rede custom (`sog-internal`/`sog-external`), isolando-o da API — risco funcional não crítico para este critério
  - Build Docker do agente não testado por timeout de rede no download do Chromium (conforme instrução)

- 2026-05-15: Wave 7 (Infra Hardening Completo) — CORREÇÃO PONTUAL VALIDADA — APROVADO
  - Serviço `backup` em `docker-compose.yml` agora possui `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]` e `deploy.resources.limits` (cpus: 0.25, memory: 128M)
  - `.gitignore` na raiz agora cobre `.env*` (linha 6) e `dados/` (linha 7)
  - Todos os demais critérios da Wave 7 permanecem como validados anteriormente

- 2026-05-15: Correções P1 pós-review (HSTS nginx + agente db wrapper) — APROVADO
  - nginx/nginx.conf: `Strict-Transport-Security` removido do bloco `listen 80`; comentado para HTTPS futuro
  - nginx/nginx-dev.conf: idem
  - agente/src/banco/db.py: wrapper de ~18 linhas importando de `sog_shared.db`; re-exporta todas as 13 funções necessárias
  - Testes agente: 50/50 passaram
  - Testes API: 28/28 passaram em 1.91s
  - Warnings: 18 preexistentes (deprecation passlib/jose), nenhum novo

- 2026-05-16: Extrator PDF + Script CLI — REPROVADO
  - Código de produção: APROVADO — funciona conforme especificado (validado manualmente)
  - Script CLI: APROVADO — extração correta do PDF real, flags --verbose e --area funcionam
  - Regressão: APROVADO — test_extrator_sentenca.py 25/25, test_parser.py 12/12
  - Bug #1 (teste): `test_extrair_texto_pdf_real` asserção rígida — PDF real contém "condenação"/"Deixo de condenar", não "condeno" literal — ALTO
  - Bug #2 (teste): `test_detectar_scanned_pdf` não mocka `os.path.exists`, retornando "Arquivo não encontrado" antes de processar — ALTO
  - Sem imports circulares, tratamento de erros adequado, nenhum arquivo existente modificado indevidamente

- 2026-05-16: Análise estática — Extrator PDF + Script CLI + Testes + Requirements — APROVADO
  - Sintaxe Python: 3/3 arquivos compilam sem erros
  - Imports: todos corretos, com fallbacks graciosos (fitz, rich, utils.logger)
  - Tratamento de erros: validado manualmente (None, vazio, int, inexistente, exceção em fitz.open)
  - Nenhuma operação de escrita/remoção/subprocess/eval/exec encontrada
  - PDF real existe em docs/processos/0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf
  - requirements.txt: pymupdf==1.24.5 presente na linha 4
  - Testes automatizados: 6/6 passaram em 13.14s
  - Bugs anteriores corrigidos: asserção flexível em test_extrair_texto_pdf_real, mock os.path.exists em test_detectar_scanned_pdf
  - Warnings: nenhum

- 2026-05-16: Extração de documentos da capa — APROVADO
  - Critério 1 (Dispositivo): todos os campos corretos — sucumbente, valor, honorários 10%, suspensão Sim, score 1.00
  - Critério 2 (Documentos da capa): 120 documentos extraídos, tipos preenchidos, IDs com 9 dígitos
  - Documentos esperados verificados: Petição Inicial (206423284), Mandado (207553631), Diligência (213349177), Comprovante de Pagamento de Custas (206426309), Decisão (206765849), Contestação (215626895)
  - Critério 3 (Regressão): 7/7 testes em test_extrator_pdf.py passaram; suite completa do agente: 57/57 passaram
  - Warnings: nenhum

- 2026-05-17: Re-validação — Correções P2/P3 extrator de custas iniciais — APROVADO
  - test_extrator_pdf.py: 13/13 passaram
  - Suite completa agente: 63/63 passaram
  - PDF real: valor_total="266,95", valor_total_centavos=26695, doc_id="206426308"
  - Correções confirmadas:
    1. _parse_valor_monetario: parsing inteiro sem float (aritmética direta)
    2. _extrair_valor_guia: regex "Valor total" primeiro; soma do detalhamento como fallback
    3. Fallback estratégia 2: cobre "comprovante de pagamento de custas" além de "guia"
    4. Dead code removido: nenhum `encontrado = False` solto
    5. Typo corrigido: `_JANELA_GUIA_EXPANDIDA` (linha 131)
    6. Teste renomeado: `test_extrair_valor_guia_sem_detalhamento` (linha 214)
  - Edge cases _parse_valor_monetario validados: R$ 1.234,56, 1234,56, R$ 266,95, 10,74, vazio, inválido, R$0,01, 1.000.000,00
  - Warnings: nenhum

- 2026-05-17: Correções P2 extrator de PDF — APROVADO
  - test_extrator_pdf.py: 15/15 passaram
  - Suite completa agente: 65/65 passaram
  - Correções confirmadas:
    1. Double-close PyMuPDF: doc.close() removido do except; permanece apenas no finally
    2. Falso positivo scanned: heurística agregada — scanned=True apenas se >80% páginas image-without-text E média texto/página < 100 chars
  - PDF real validado: scanned=False, valor_total="266,95", num_paginas=722, erro=''
  - Warnings: nenhum

- 2026-05-17: Re-validação — Correções P3 extrator de PDF — APROVADO
  - test_extrator_pdf.py: 15/15 passaram
  - Suite completa agente: 65/65 passaram
  - Correções confirmadas:
    1. resultado_base inclui "custas_iniciais" com contrato uniforme (linha 574)
    2. Threshold scanned: >= 0.8 (linha 638) — PDFs com exatamente 80% páginas image-only marcados como scanned
    3. Comentário explicativo adicionado na heurística de scanned (linhas 631-633)
  - PDF real validado: scanned=False, valor_total="266,95", num_paginas=722, erro=''
  - Warnings: nenhum

- 2026-05-18: Fase 1 (Serviço longo + comunicação SQLite) — APROVADO
  - Testes API: 37/37 passaram em 1.30s
  - Build frontend: passou sem erros TypeScript
  - Testes frontend: 124/124 passaram
  - py_compile agente: servico.py e pipeline.py — sintaxe OK
  - Schema SQLite: validado em banco temporário, sem duplicações
  - Duplicações: schema.sql (1x), db.py funções (1x cada), app.py router (1x)
  - run_agente.sh: executável, shebang #!/bin/bash correto
  - Warnings: 23 preexistentes (deprecation jose/jwt), nenhum novo

- 2026-05-18: Fases 2 e 3 (AuthManager + Storage State + CR-002 Escaping CSS) — APROVADO
  - Testes agente: 71/71 passaram (inclui 6 novos testes test_css_escape.py)
  - Testes API: 37/37 passaram em 2.51s
  - Build frontend: passou sem erros TypeScript
  - Testes frontend: 124/124 passaram
  - py_compile: auth_manager.py, css_escape.py, servico.py — sintaxe OK
  - Duplicação escape_for_css em pje.py: 0 ocorrências (função local removida)
  - Import css_escape em pje.py: 1 ocorrência (linha 30)
  - retry.py importa ReautenticacaoNecessariaError: 3 ocorrências (linha 16)
  - PlaywrightClient usa AuthManager: _auth property, fechar() delega
  - pje.py e sistjweb.py: garantir_autenticado() e _esta_logado() usam AuthManager
  - servico.py: captura ReautenticacaoNecessariaError, estados autenticando/aguardando_login/executando
  - selectors.py: templates transformados em funções geradoras (pje_etiqueta_link, pje_link_processo, pje_doc_link_nome)
  - Warnings: 23 preexistentes (deprecation jose/jwt), nenhum novo

- 2026-05-18: Fase 4 (Integração custas iniciais PDF no pipeline) — APROVADO
  - Testes agente: 74/74 passaram em 55.16s
  - Testes API: 37/37 passaram em 1.50s
  - Build frontend: passou sem erros TypeScript
  - Testes frontend: 124/124 passaram em 18.81s
  - py_compile: pje.py, pipeline.py, parser.py — sintaxe OK
  - baixar_documento_pdf: existe em pje.py (linha 507), com retry e tratamento de exceção
  - custas_iniciais propagado: pipeline.py (_construir_payload linha 77, extração linhas 161-201, processar_documentos linha 203) e parser.py (processar_documentos linha 39, mesclagem linhas 83-90)
  - Deduplicação: numero_guia usado como chave em set, tanto em pipeline.py (linhas 83-87) quanto parser.py (linhas 84-88); custas sem numero_guia adicionadas diretamente
  - Testes deduplicação: test_processar_documentos_deduplica_custas_por_guia, test_processar_documentos_com_custas_iniciais, test_processar_documentos_custas_iniciais_sem_numero_guia
  - Warnings: 23 preexistentes (deprecation jose/jwt), nenhum novo
