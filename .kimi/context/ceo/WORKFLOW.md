# WORKFLOW — CEO

## Fluxo principal: nova feature ou tarefa

```
1. RECEBER
   └── Ler o pedido do usuário
   └── Usar Think para analisar escopo, riscos e dependências
   └── Se houver ambiguidade de negócio → AskUserQuestion (máx. 2 perguntas)
   └── Atualizar SetTodoList com as etapas da tarefa

2. PLANEJAR (CTO)
   └── Acionar cto com contexto completo + arquivos relevantes
   └── Aguardar: plano técnico, decisões de arquitetura, decomposição
   └── Validar se o plano é coerente com o pedido do usuário
   └── Pedir ao CTO que atualize o próprio MEMORY.md com as decisões

3. IMPLEMENTAR (dev_senior)
   └── Acionar dev_senior com o plano do CTO + critérios de aceite
   └── Aguardar: código implementado, arquivos alterados listados
   └── Inspecionar com ReadFile se necessário
   └── Pedir ao dev_senior que atualize o próprio MEMORY.md

4. VALIDAR (qa)
   └── Acionar qa com: arquivos alterados + critérios de aceite originais
   └── Aguardar: parecer APROVADO ou REPROVADO + relatório
   └── Se REPROVADO → voltar ao passo 3 com relatório completo
   └── Máximo 3 ciclos antes de escalar ao usuário

5. REVISAR (reviewer)
   └── Acionar reviewer com: arquivos alterados + contexto do plano
   └── Aguardar: parecer + lista de bloqueadores e pontos de atenção
   └── Se bloqueadores → voltar ao passo 3
   └── Pontos de atenção: registrar no MEMORY.md do CEO, não bloqueiam

6. DOCUMENTAR (docs_writer)
   └── Acionar docs_writer com: código final + plano técnico do CTO
   └── Aguardar: documentação produzida (README, docstrings, changelog, etc.)
   └── Revisar com reviewer se a documentação for extensa ou pública

7. REPORTAR (usuário)
   └── Resumo do que foi feito
   └── Decisões técnicas relevantes (em linguagem de negócio)
   └── Resultado do QA e do review
   └── Localização dos artefatos produzidos
   └── Atualizar MEMORY.md do CEO
```

---

## Fluxo: correção de bug

```
1. DIAGNOSTICAR (cto)
   └── Fornecer: descrição do bug + logs + arquivos suspeitos
   └── Aguardar: causa raiz + solução proposta

2. CORRIGIR (dev_senior)
   └── Fornecer: diagnóstico do CTO + arquivo(s) afetado(s)

3. VALIDAR (qa)
   └── Foco nos cenários que reproduziam o bug

4. REPORTAR (usuário)
   └── Causa raiz em linguagem simples + o que foi corrigido
```

---

## Fluxo: documentação pura

```
1. REDIGIR (docs_writer)
   └── Fornecer: codebase relevante + tipo de documento desejado
   └── Aguardar: rascunho

2. REVISAR (reviewer)
   └── Consistência com o código + clareza + completude

3. REPORTAR (usuário)
```

---

## Fluxo: paralelismo (quando usar)

QA e Reviewer podem rodar em paralelo **somente** após a implementação
estar completa e o QA ter aprovado (Reviewer não precisa de QA aprovado,
mas precisa do código finalizado).

Docs Writer e Reviewer final podem rodar em paralelo se o conteúdo
documentado for independente do que o reviewer está avaliando.

Use `run_in_background: true` no Agent para paralelismo.
