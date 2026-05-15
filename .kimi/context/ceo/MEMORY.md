# MEMORY — CEO

> Este arquivo é dinâmico. O CEO deve atualizá-lo ao longo dos projetos,
> registrando decisões estratégicas, padrões identificados e aprendizados
> que devem persistir entre sessões.

---

## Projetos ativos

### SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)
- **Iniciado em:** 2026-05-15
- **Stack:** Python 3.12 + Playwright (agente), FastAPI + SQLite (API), React 18 + Vite + Tailwind (frontend), Docker Compose + Nginx (infra)
- **Status:** em andamento — code review enterprise-grade concluído
- **Última ação:** Code review completo em 4 waves (Agente, API, Frontend, Cross-cutting). Relatório enterprise-grade consolidado e entregue.
- **Próximo passo:** Correção dos 15 bloqueadores críticos identificados no relatório. Aguardando direção do usuário.

---

## Decisões estratégicas tomadas

- **2026-05-15:** Code review do SOG revelou 98 issues (15 críticas, 38 altas, 29 médias, 16 baixas). Veredicto global: REPROVADO para produção. Correção dos bloqueadores é pré-requisito para qualquer deploy.
- **2026-05-15:** Identificada necessidade de migração de SQLite para PostgreSQL como deuda técnica estrutural (race conditions, HA, backups).
- **2026-05-15:** Armazenamento de JWT em localStorage foi classificado como bloqueador de segurança. Migração para httpOnly cookies é mandatória antes de produção.

---

## Padrões de delegação aprendidos

- **Reviewer em background:** Funciona bem para tarefas longas e independentes, mas o timeout padrão (15min) pode ser insuficiente para reviews extensos. Recomenda-se usar timeout=1800s.
- **Reviewer em foreground:** Mais confiável para garantir entrega quando o resultado é bloqueante. Usar para waves finais ou quando o background falhar.
- **Docs_writer:** Não performa bem com prompts extremamente longos (>3000 palavras de contexto). Para documentos enterprise-grade extensos, o CEO deve consolidar diretamente a partir dos outputs dos agents especializados.
- **Code review enterprise-grade:** Dividir em waves por módulo (Agente, API, Frontend, Infra) e depois consolidar em documento único é a abordagem mais eficaz. Cada wave deve ter critérios explícitos e formato de saída padronizado.

---

## Preferências do usuário/cliente

- Solicitou relatório "enterprise grade" para code review completo do projeto.
- Sistema lida com dados judiciais sensíveis (processos, CPF/CNPJ, valores) — segurança e LGPD são prioridades absolutas.

---

## Log de entregas

- **2026-05-15:** Code Review Enterprise-Grade do SOG — 4 waves, 61 artefatos revisados, 98 issues identificados. Relatório consolidado em `docs/code-review-enterprise-report.md`. Todos os módulos reprovados (bloqueadores críticos presentes).
