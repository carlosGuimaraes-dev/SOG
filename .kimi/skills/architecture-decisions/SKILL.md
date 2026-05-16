---
name: architecture-decisions
description: Use quando precisar registrar, revisar ou tomar decisões arquiteturais significativas. Aplica-se a escolha de padrões, bibliotecas, estruturas de dados, divisão de serviços e mudanças de arquitetura.
---

# Decisões Arquiteturais e ADRs

## Resumo

Decisões arquiteturais são escolhas difíceis de mudar posteriormente. Documentá-las com ADRs (Architecture Decision Records) cria um histórico rastreável de porquês, não apenas de oquês. Cada ADR captura contexto, alternativas consideradas e consequências — facilitando revisão e reversão quando necessário.

## Quando usar

- Antes de introduzir uma nova dependência, framework ou padrão de projeto
- Ao dividir ou unir serviços/módulos
- Quando uma decisão contradiz uma escolha anterior
- Ao arquivar uma discussão que já ocorreu informalmente (Slack, reunião)
- Durante revisão de código que levanta questões arquiteturais

## Padrões principais

### Formato ADR

Estrutura mínima de um ADR:

1. **Título** — identificador numérico + nome descritivo
2. **Contexto** — forças, restrições, pressões que levaram à decisão
3. **Decisão** — afirmação clara no formato "Decidimos X em vez de Y/Z porque..."
4. **Consequências** — positivas, negativas e neutras (trade-offs explícitos)
5. **Status** — proposto / aceito / deprecado / superseded por ADR-NNN

```markdown
# ADR-012: Uso de SQLite em vez de PostgreSQL para dados locais

## Contexto
- Volume esperado < 1GB por instalação
- Deploy em ambientes sem infraestrutura de banco dedicada
- Requisito de backup simples (arquivo único)

## Decisão
Usaremos SQLite para armazenamento local do agente.

## Consequências
- Positivas: zero configuração, backup por cópia de arquivo
- Negativas: sem concorrência de escrita avançada; se escalar, migrar para PostgreSQL
- Neutras: SQL padrão, ORM funciona igual

## Status
Aceito
```

### Quando escrever ADR

| Situação | Escrever ADR? |
|----------|---------------|
| Escolha que afeta > 1 módulo | Sim |
| Dependência nova com lock-in | Sim |
| Padrão de código (naming, lint) | Não (use style guide) |
| Correção de bug isolado | Não |
| Mudança de versão de biblioteca | Apenas se houver breaking change significativo |

### Catalogação de decisões

Mantenha ADRs em `docs/adres/` ou `adr/` na raiz do projeto.

```
docs/adres/
  001-uso-de-fastapi.md
  002-sqlite-para-dados-locais.md
  003-playwright-para-automacao.md
```

Use identificadores sequenciais. Não reutilize números de ADRs arquivados.

### Trade-offs explícitos

Sempre documente o que se ganha e o que se perde. Exemplos:

- "Ganhamos simplicidade de deploy; perdemos escalabilidade horizontal imediata"
- "Reduzimos dependências externas; assumimos manutenção do componente"

Se não houver trade-offs negativos, desconfie da análise.

### Reversibilidade de decisões

Classifique cada decisão:

- **Reversível em horas** (mudança de biblioteca utilitária) → ADR opcional
- **Reversível em semanas** (mudança de ORM) → ADR obrigatório
- **Irreversível ou muito cara** (escolha de linguagem) → ADR + revisão formal

Documente condições de reversão: "Se o volume de dados ultrapassar 10GB, revisar ADR-012".

### Revisão de ADRs

- Reveja ADRs a cada 6 meses ou a cada release maior
- Marque como `deprecated` quando uma decisão não é mais válida
- Use `superseded by ADR-NNN` para encadear evolução
- Arquive, não delete — o histórico é tão importante quanto a decisão atual

## Exemplos

### Escrevendo um ADR durante code review

Durante revisão, um revisor questiona: "Por que não usamos Celery ao invés de cron puro?"

Resposta do autor:

```markdown
# ADR-007: Agendamento via cron em vez de Celery

## Contexto
O agente executa tarefas em intervalos fixos (a cada hora). Não há
necessidade de filas, retries complexos ou workers paralelos no
momento.

## Decisão
Usar cron simples via container. Revisar se surgir requisito de
tarefas assíncronas com retry e prioridade.

## Consequências
- Positivas: menos infraestrutura, menos dependências
- Negativas: sem retry automático, sem dashboard de filas
- Gatilho de revisão: mais de 3 tarefas com lógica de retry
```

### Atualizando um ADR obsoleto

```markdown
# ADR-003: Automação com Selenium

## Status
Deprecated — superseded by ADR-015

## Motivo da depreciação
Selenium apresentou instabilidade com elementos shadow DOM no
PJe. Playwright resolveu o problema com esperas automáticas mais
robustas (ver ADR-015).
```

## Anti-patterns

- **ADR genérico** — "Usamos boas práticas" não é uma decisão arquitetural
- **Sem consequências negativas** — toda decisão tem custo; omiti-lo é desonesto
- **Status sempre "aceito"** — ADRs nunca revisitados perdem o valor histórico
- **Contexto ausente** — "Decidimos usar X" sem explicar por que Y foi descartado
- **Muito longo** — ADR deve caber em 1-2 páginas; discussões longas vão para apêndice
