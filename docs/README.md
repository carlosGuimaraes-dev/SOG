# Documentação do SOG

## Arquivos canônicos

- `../README.md`: visão geral e onboarding inicial
- `architecture.md`: componentes, fluxo operacional e persistência
- `api.md`: contratos principais consumidos pelo dashboard
- `operacao-local-docker.md`: execução local em Docker e diferenças entre estado atual e direção arquitetural
- `../frontend/README.md`: comportamento atual do dashboard

## Artefatos históricos ou de apoio

Estes arquivos continuam úteis como contexto, mas não devem ser lidos como
espelho fiel do estado atual do sistema:

- `PRD.md`
- `../SYMPHONY.md`
- `regras_custas_tjdft.md`
- `agents/`
- `../.kimi/`
- `../.symphony/`

## Arquivos consolidados nesta auditoria

- `todo-frontend.md`: plano técnico histórico do pacote de melhorias do dashboard
- `TODO_frontend.md`: apontador curto para o plano técnico e para a documentação atual do frontend
- `code-review-enterprise-report.md`: relatório enterprise canônico
- `ENTERPRISE_CODE_REVIEW_REPORT.md`: apontador para o relatório canônico
- `code-review-fixes.md`: plano técnico das correções do code review
- `correcoes-code-review.md`: resumo das correções aplicadas e pendências declaradas

## Critério de leitura

- Para comportamento implementado: prefira código, testes e os arquivos canônicos acima.
- Para contexto de decisão antiga: consulte os artefatos históricos explicitamente rotulados como tal.
- Para regras TJDFT: não trate templates ou notas internas como verdade de domínio sem validação externa.
