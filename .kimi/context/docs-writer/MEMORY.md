# MEMORY — Docs Writer

> Arquivo dinâmico. Registre convenções de documentação adotadas,
> padrões de escrita definidos e lacunas identificadas entre o código
> e a documentação existente.

---

## Convenções de documentação do projeto

- Idioma: português para documentação interna/enterprise
- Formato: Markdown com tabelas extensivas para rastreabilidade
- Estilo: tom enterprise — objetivo, quantificado, sem alarmismo mas sem minimizar riscos
- IDs de issue: prefixo por severidade (CRIT-, HIGH-, MED-, LOW-) + categoria (SEC, ARC, PERF, DEV, FE)

---

## Documentação existente (mapa)

- `ENTERPRISE_CODE_REVIEW_REPORT.md` — Relatório enterprise consolidado de 4 waves de code review (2026-05-15)
  - Seções: Executive Summary, Risk Heat Map, Critical Issues (13), High Issues (15), Medium/Low por categoria, Positive Findings, Strategic Roadmap (Immediate/Short-term/Medium-term), Compliance & Governance, Appendices (Scorecards, Matriz de Responsabilidade, Referências)

---

## Lacunas de documentação identificadas

- README.md principal do projeto não documenta riscos de segurança conhecidos
- Ausência de guia de contribuição (CONTRIBUTING.md)
- Ausência de CHANGELOG.md
- Ausência de ADRs para decisões arquiteturais críticas (SQLite vs PostgreSQL, localStorage vs httpOnly cookies)
- Documentação de deploy não cobre hardening de containers
- Variáveis de ambiente não documentam riscos de segurança associados

---

## Histórico de documentações produzidas

- 2026-05-15: `ENTERPRISE_CODE_REVIEW_REPORT.md` — consolidação enterprise-grade de 4 waves de code review (Agente, API, Frontend, Infra)
