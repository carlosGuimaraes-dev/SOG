# MEMORY — CEO

> Arquivo dinâmico. Atualizado ao longo dos projetos registrando decisões
> estratégicas, padrões identificados e aprendizados entre sessões.

---

## Projetos ativos

### SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)
- **Iniciado em**: 2026-05-15
- **Stack**: Python 3.12 + Playwright (Agente), FastAPI + SQLite (API), React 18 + Vite (Frontend), Docker Compose + Nginx (Infra)
- **Status**: 95/98 issues corrigidas e aprovadas. Documentação entregue.
- **Última ação**: Wave 7 aprovada, ressalvas P1 do reviewer corrigidas e validadas, documentação produzida.
- **Próximo passo**: Reavaliação formal do code review (score atual estimado ~8.0/10) antes do deploy em produção com dados reais.

---

## Decisões estratégicas tomadas

- **2026-05-15**: Implementar todas as 98 issues do code review enterprise, divididas em 8 waves incrementais.
- **2026-05-15**: Wave 8 (PostgreSQL) adiada — volume atual < 50 processos/dia; SQLite com WAL + backup sidecar é adequado.
- **2026-05-15**: Rate limiting usa `slowapi` em memória (sem Redis) até escala horizontal justificar.
- **2026-05-15**: httpOnly cookies com `Secure=false` em dev, `Secure=true` em produção — requer TLS ativo no ambiente de produção.

---

## Padrões de delegação aprendidos

- **QA performa melhor** quando recebe os caminhos exatos dos arquivos alterados e critérios de aceite mensuráveis.
- **DevOps precisa de instrução explícita** para NÃO fazer build do Docker durante a implementação (evita timeout em downloads pesados como Chromium).
- **Frontend precisa de contrato claro** com backend (endpoints, formato de resposta) antes de implementar.
- **Wave 6 (pacote compartilhado)** exige verificação pós-implementação de que TODOS os consumidores (agente + API) realmente usam o pacote, não mantêm cópia local.
- **Reviewer identifica ressalvas que QA não pega** — especialmente em arquitetura e inconsistências entre módulos.

---

## Preferências do usuário / cliente

- Decisões rápidas; não gosta de bloqueios burocráticos.
- Valida argumentos técnicos antes de decidir escopo (ex: questionou Wave 8 antes de aprovar).
- Prefere adiar complexidade desnecessária quando o volume de negócio não justifica.

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
