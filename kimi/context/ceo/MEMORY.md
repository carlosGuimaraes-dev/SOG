# MEMORY — CEO

> Arquivo dinâmico. Atualizado ao longo dos projetos registrando decisões
> estratégicas, padrões identificados e aprendizados entre sessões.

---

## Projetos ativos

### SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)
- **Iniciado em**: 2026-05-15
- **Stack**: Python 3.12 + Playwright (Agente), FastAPI + SQLite (API), React 18 + Vite (Frontend), Docker Compose + Nginx (Infra)
- **Status**: 95/98 issues corrigidas e aprovadas. Documentação entregue. Extrator de PDF com extração de custas iniciais implementado. Integração PJe/SISTJWEB expandida com fila de tarefas, rotas novas e executor do agente.
- **Última ação**: Integração PJe/SISTJWEB iniciada com rotas `/pje`, `/sistj`, `/processos` e `/dashboard`, além de handlers do agente para consulta, download, preenchimento, aprovação, reprocessamento e reautenticação.
- **Próximo passo**: Validar o fluxo end-to-end na UI ou avançar para a próxima onda do plano conforme prioridade do usuário.

---

## Decisões estratégicas tomadas

- **2026-05-15**: Implementar todas as 98 issues do code review enterprise, divididas em 8 waves incrementais.
- **2026-05-15**: Wave 8 (PostgreSQL) adiada — volume atual < 50 processos/dia; SQLite com WAL + backup sidecar é adequado.
- **2026-05-15**: Rate limiting usa `slowapi` em memória (sem Redis) até escala horizontal justificar.
- **2026-05-15**: httpOnly cookies com `Secure=false` em dev, `Secure=true` em produção — requer TLS ativo no ambiente de produção.
- **2026-05-16**: Biblioteca de PDF escolhida: `pymupdf` (fitz) — performance superior, extrai texto com bbox, OCR integrado via Tesseract.

---

## Padrões de delegação aprendidos

- **QA performa melhor** quando recebe os caminhos exatos dos arquivos alterados e critérios de aceite mensuráveis.
- **DevOps precisa de instrução explícita** para NÃO fazer build do Docker durante a implementação (evita timeout em downloads pesados como Chromium).
- **Frontend precisa de contrato claro** com backend (endpoints, formato de resposta) antes de implementar.
- **Wave 6 (pacote compartilhado)** exige verificação pós-implementação de que TODOS os consumidores (agente + API) realmente usam o pacote, não mantêm cópia local.
- **Reviewer identifica ressalvas que QA não pega** — especialmente em arquitetura e inconsistências entre módulos.
- **Agentes de implementação podem dar timeout** em tasks grandes. Dividir em micro-tarefas (ex: só o módulo, depois CLI+testes) funciona.
- **Não repetir SetTodoList sem progresso real** — o sistema detecta e bloqueia. Fazer ação real antes de atualizar status.
- **Investigação de PDF via subagente pode dar timeout** — para análise de arquivos grandes, preferir Shell direto ou extrator existente.
- **Ressalvas P2 devem ser corrigidas antes de seguir** — o reviewer encontrou issues reais (float em monetário, priorização de valor, fallback) que melhoraram a qualidade do código.
- **Ressalvas P3 são rápidas de corrigir** — geralmente documentação, comentários, ajustes de threshold. Vale a pena fazer para manter a régua alta.

---

## Preferências do usuário / cliente

- Decisões rápidas; não gosta de bloqueios burocráticos.
- Valida argumentos técnicos antes de decidir escopo (ex: questionou Wave 8 antes de aprovar).
- Prefere adiar complexidade desnecessária quando o volume de negócio não justifica.
- Espera que o CEO delegue e cobre resultados, não execute código diretamente.
- Compartilha conhecimento de domínio operacional (ex: como localizar guia de pagamento no PDF do PJe) para orientar implementação técnica.

---

## Log de entregas

- **2026-05-15**: Wave 1 — Segurança Crítica I (Infra + Auth Core) — aprovada por QA.
- **2026-05-15**: Wave 2 — Segurança Crítica II (Agente + Playwright) — aprovada por QA.
- **2026-05-15**: Wave 3 — Auth Cross-Cutting (httpOnly cookies + Screenshots API) — aprovada por QA após correção de endpoints /auth/me e /auth/logout.
- **2026-05-15**: Wave 4 — Backend API (Concorrência, Paginação, Models) — aprovada por QA.
- **2026-05-15**: Wave 5 — Frontend (Refatoração, UX, Testes) — aprovada por QA.
- **2026-05-15**: Wave 6 — Arquitetura Python (Pacote shared, SRP) — aprovada por QA.
- **2026-05-15**: Wave 7 — Infra Hardening (Containers non-root, nginx limits) — aprovada por QA após correção de backup hardening + .gitignore.
- **2026-05-15**: Reviewer — APROVADO COM RESSALVAS. Ressalvas P1 (HSTS em HTTP, db.py duplicado no agente) corrigidas e re-validadas por QA.
- **2026-05-15**: Documentação — `docs/correcoes-code-review.md` produzida pelo docs_writer.
- **2026-05-16**: Extrator de PDF — Módulo `extrator_pdf.py` + script CLI `testar_pdf.py` + testes + docs. Aprovado por QA (6/6 testes passaram) e Reviewer (APROVADO COM RESSALVAS P2/P3).
- **2026-05-17**: Extração de custas iniciais do PDF — Feature aditiva ao `extrator_pdf.py` que localiza a guia de pagamento pelo `doc_id` da capa e extrai valor total + detalhamento por item. Aprovado por QA (13/13 testes, 63/63 suite completa) e Reviewer (APROVADO após correções P2: parsing inteiro de monetário, priorização de regex "Valor total", fallback estendido para comprovantes). Documentação atualizada.
- **2026-05-17**: Correções P2/P3 do extrator de PDF — (1) Double-close PyMuPDF eliminado (`doc.close()` apenas no `finally`); (2) Falso positivo scanned corrigido (heurística agregada: ≥80% páginas image-only E média <100 chars/página); (3) Contrato uniforme em erro (`resultado_base` inclui `"custas_iniciais"`); (4) Threshold inclusivo (`>= 0.8`); (5) Comentários explicativos. Aprovado por QA (15/15 testes, 65/65 suite completa) e Reviewer (APROVADO COM RESSALVAS P3). Documentação atualizada em `docs/correcoes-code-review.md` §9.2 e `docs/testar-pdf.md`.
- **2026-05-19**: Integração PJe/SISTJWEB — fila de tarefas e rotas de entrada publicadas na API; executor do agente expandido com handlers read-only, write e reprocessamento; status de sessão consolidado via cache da última tarefa verificada. Aprovado por QA (138/138 testes).
- **2026-05-19**: Wave 4 — stale detection, cancelamento cooperativo de tarefas em execução, reautenticação explícita via navegador visível e teste sequencial de 5 tarefas sem deadlock. Aprovado por QA (144/144 testes).
