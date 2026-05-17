# MEMORY — Docs Writer

> Arquivo dinâmico. Registre convenções de documentação, mapa de docs
> existentes e lacunas identificadas.

---

## Convenções de documentação do projeto

- Idioma: português para docs internas/técnicas.
- Formato: Markdown puro com tabelas para checklists e matrizes.
- Estilo de changelog: N/A (usamos documento de correções incremental).
- Docstrings: Google style (Args, Returns, Raises) quando aplicável.
- Exemplos de código: sempre verificados contra o código real antes de publicar.

---

## Mapa de documentação existente

- `README.md` — visão geral + instalação + fluxo de trabalho (revisado em 2026-05-17)
- `docs/code-review-enterprise-report.md` — relatório original do code review (555 linhas, confidencial)
- `.kimi/context/cto/code-review-fixes.md` — plano técnico das 8 waves (752 linhas)
- `docs/correcoes-code-review.md` — correções técnicas das 95 issues
- `docs/testar-pdf.md` — **documentação produzida nesta sessão** (guia do script CLI `testar_pdf.py`)

---

## Lacunas de documentação identificadas

- `docs/api.md` — Referência completa de API REST ainda não existe (endpoints estão parcialmente cobertos em `correcoes-code-review.md`)
- `docs/adr/` — Nenhum ADR registrado. Decisões arquiteturais (httpOnly cookies, shared package, adiar PostgreSQL) estão documentadas apenas em `correcoes-code-review.md`.
- `CONTRIBUTING.md` — Não existe guia de contribuição.
- `CHANGELOG.md` — Não existe.
- Documentação do agente (Playwright) — `agente/src/modulos/` não tem README; conhecimento está disperso nos docstrings.
- Documentação de deploy em produção — o `docker-compose.yml` está documentado, mas não existe runbook de failover/backup.

---

## Histórico de documentações produzidas

- 2026-05-15: `docs/correcoes-code-review.md` — Resumo executivo, guia de configuração, decisões arquiteturais, como rodar, checklist de segurança e roadmap das 95 correções do code review enterprise.
- 2026-05-16: `docs/testar-pdf.md` — Guia de uso do script CLI `testar_pdf.py`: instalação, flags, interpretação de resultados, códigos de saída e limitações.
- 2026-05-17: `docs/testar-pdf.md` — Atualizado com campo "Custas Iniciais", exemplo JSON real e mecanismo de extração.
- 2026-05-17: `docs/correcoes-code-review.md` — Nova seção 9 "Entregas Incrementais (pós-code-review)" registrando a feature de extração de custas iniciais do PDF.
- 2026-05-17: `README.md` — Atualizado: fluxo de trabalho menciona extração de custas iniciais; estrutura do projeto inclui `extrator_pdf.py` e `extrator_sentenca.py`; testes incluem `test_extrator_pdf.py`.
- 2026-05-17: `docs/correcoes-code-review.md` — Subseção 9.2 adicionada: registra 2 correções P2 (double-close PyMuPDF, falso positivo scanned) e 3 ajustes P3 (contrato uniforme, threshold >= 0.8, comentário explicativo) no extrator de PDF.
- 2026-05-17: `docs/testar-pdf.md` — Seção "Limitações" atualizada para documentar a heurística agregada de scanned detection (≥80% páginas image-only + média < 100 chars).
