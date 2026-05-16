---
name: orchestration-patterns
description: Use ao coordenar múltiplos agentes, ferramentas ou etapas de trabalho. Aplica-se a pipelines, workflows multi-step, delegação entre agentes especializados e loops de feedback.
---

# Padrões de Orquestração de Agentes

## Resumo

Orquestração é o gerenciamento deliberado de fluxos de trabalho entre agentes e ferramentas. Um orquestrador eficaz define escopo claro, passa contexto completo, estabelece critérios de aceite e limita ciclos de feedback — evitando loops infinitos e delegação vazia.

## Quando usar

- Um único agente não tem todas as habilidades necessárias
- Tarefas exigem sequência ordenada de passos com verificação intermediária
- Diferentes partes de uma tarefa exigem contextos ou ferramentas distintas
- É necessário revisar ou refinar resultados antes de prosseguir
- Há risco de operação destrutiva que precisa de confirmação

## Padrões principais

### Fluxos de trabalho

Divida tarefas complexas em etapas sequenciais com entregáveis definidos:

```
Entrada → [Etapa 1] → Verificação → [Etapa 2] → Verificação → [Etapa 3] → Saída
```

Regras:
- Cada etapa tem um único objetivo mensurável
- Entregáveis de uma etapa são entrada da próxima
- Falha em qualquer etapa para o fluxo (fail-fast)
- Documente pré-condições e pós-condições de cada etapa

Exemplo de fluxo para análise de custas:

```
1. Extrair dados brutos do PJe
   → Verificar: HTML contém tabela de custas
2. Parsear e estruturar dados
   → Verificar: JSON válido com campos obrigatórios
3. Persistir no banco
   → Verificar: registro criado com sucesso
4. Gerar relatório
   → Verificar: arquivo PDF gerado e legível
```

### Delegação com contexto completo

Ao delegar para outro agente, forneça:

1. **Objetivo claro** — o que deve ser entregue
2. **Contexto mínimo necessário** — não mais, não menos
3. **Restrições** — o que não fazer
4. **Formato de saída esperado** — schema ou template
5. **Critério de aceite** — quando a tarefa está completa

```markdown
## Delegação: Revisar código de extração de PDF

### Contexto
O módulo `extractor.py` extrai tabelas de PDFs do TJDFT.
Última mudança: adição de suporte a células mescladas.

### Objetivo
Revisar a função `extrair_tabela()` em `extractor.py`.

### Restrições
- Não alterar a interface pública (assinatura da função)
- Não adicionar novas dependências

### Formato de saída
Lista de problemas encontrados, cada um com:
- severidade (critical/warning/suggestion)
- linha
- descrição
- sugestão de correção

### Critério de aceite
Lista entregue e todos os itens critical revisados.
```

### Critérios de aceite

Todo fluxo ou delegação deve ter critérios binários:

- Ruim: "melhorar o código" → subjetivo
- Bom: "reduzir complexidade ciclomática de 15 para < 10" → mensurável
- Bom: "todos os testes existentes passam + 3 novos testes para edge cases" → verificável

Use verificação automática quando possível: testes, lint, type check.

### Feedback loops

Use loops de feedback para refinar resultados:

```
Agente A produz → Verificação → Se falhar → Feedback → Agente A refina → Verificação
```

Regras:
- Feedback deve ser específico e acionável
- Cite exemplos concretos, não generalizações
- Diferencie entre erro factual (corrigir) e estilo (discutir)

Exemplo de feedback eficaz:

```markdown
## Feedback sobre parser de custas

### Problema
A função retorna `None` para 3 dos 50 PDFs de teste.

### Casos específicos
- `processo_1234.pdf`: tabela com 2 colunas ao invés de 3
- `processo_5678.pdf`: célula vazia na coluna "valor"

### Ação esperada
Adicionar tratamento para:
1. Tabelas com número variável de colunas
2. Células vazias (usar 0.0 para valor)

### Validação
Executar contra os 50 PDFs de teste; taxa de sucesso deve ser 100%.
```

### Máximo de 3 ciclos

Limite loops de feedback a 3 iterações:

| Ciclo | Expectativa |
|-------|-------------|
| 1 | Implementação inicial |
| 2 | Correção de problemas óbvios |
| 3 | Ajustes finos |

Se após 3 ciclos o resultado não é aceitável:
- Reavalie a decomposição da tarefa
- Verifique se o contexto inicial era suficiente
- **Escale para usuário** — não continue em loop

### Quando escalar para usuário

Escale imediatamente quando:

- Ambiguidade de requisito não resolvível pelo agente
- Decisão de trade-off que afeta arquitetura ou custo
- Mais de 3 ciclos de feedback sem convergência
- Operação destrutiva (deletar dados, remover serviços)
- Inconsistência entre instruções e comportamento esperado

Mensagem de escalação deve incluir:

```markdown
## Escalation

### Contexto
Tentativa de refatorar o módulo X para usar padrão Y.

### Bloqueio
Conflito entre requisitos:
- Requisito A pede alta performance (padrão Y lento)
- Requisito B pede simplicidade (padrão Z complexo)

### Decisão necessária
Qual requisito tem prioridade? Ou há terceira opção?

### Opções consideradas
1. Manter padrão atual (atende B, viola A)
2. Migrar para Y (atende A, viola B)
3. Híbrido (complexidade média, atende ambos parcialmente)
```

## Exemplos

### Orquestração de pipeline de deploy

```
Etapa 1: Build
- Agente: builder
- Input: código fonte
- Output: imagem Docker
- Critério: build sem erros, imagem < 500MB

Etapa 2: Testes
- Agente: tester
- Input: imagem Docker
- Output: relatório de testes
- Critério: 100% de testes passando

Etapa 3: Deploy staging
- Agente: deployer
- Input: imagem aprovada
- Output: URL de staging
- Critério: health check passa

Etapa 4: Validação
- Agente: validator
- Input: URL de staging
- Output: aprovação/rejeição
- Critério: smoke tests passam

Se qualquer etapa falhar → feedback ao agente anterior → retry (máx 3)
Se retry esgotar → escalar para usuário com logs
```

### Feedback loop refinado

```
Ciclo 1: Agente gera código de extração
→ Verificação: falha em 5 de 50 PDFs

Ciclo 2: Feedback com lista dos 5 PDFs e erro específico
→ Agente corrige
→ Verificação: falha em 1 de 50 PDFs

Ciclo 3: Feedback com o 1 PDF restante
→ Agente corrige
→ Verificação: 50/50 passam → aceito
```

## Anti-patterns

- **Delegação sem contexto** — "arruma isso" sem especificar o quê, por quê ou como medir
- **Loops infinitos** — mais de 3 ciclos sem convergência; falta de critério de parada
- **Critérios subjetivos** — "melhorar" ou "otimizar" sem métrica
- **Feedback genérico** — "não está bom, tente de novo" sem detalhes
- **Escalar tarde demais** — insistir em resolver ambiguidade sem usuário por 10 ciclos
- **Orquestração desnecessária** — delegar tarefa que um único agente resolve em 1 passo
- **Falha de verificação** — passar para próxima etapa sem validar a anterior
