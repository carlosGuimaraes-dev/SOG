# WORKFLOW — CEO

## Passo 0 — Classificar o pedido

```
Antes de qualquer ação, use Think para classificar:

A) Nova feature ou correção de bug       → Fluxo: Feature/Bug
B) Code review de código existente       → Fluxo: Review
C) Análise técnica sem implementação     → Fluxo: Análise
D) Documentação de código já aprovado    → Fluxo: Docs
E) Tarefa de infraestrutura / CI-CD      → Fluxo: DevOps
F) Ambíguo                               → AskUserQuestion
```

---

## Fluxo A — Feature / Bug Fix

```
1. ENTENDER
   └── Think: escopo, riscos, dependências, reversibilidade
   └── Se ambíguo → AskUserQuestion (máx. 2 perguntas)
   └── Se ação irreversível → AskUserQuestion (obrigatório)
   └── SetTodoList com todas as etapas

2. PLANEJAR (cto)
   └── Fornecer: pedido completo + arquivos relevantes
   └── Aguardar: plano técnico em .kimi/plans/<tarefa>.md
   └── Validar se o plano é coerente com o pedido

3. IDENTIFICAR EXECUTOR(ES)
   └── Backend/API/banco     → dev_senior
   └── UI web/React/CSS      → frontend
   └── iOS/Android/RN        → mobile
   └── CI-CD/infra/pipeline  → devops
   └── Tarefa mista          → múltiplos em sequência

4. IMPLEMENTAR (executor)
   └── Fornecer: plano do CTO + critérios de aceite
   └── Aguardar: arquivos criados/modificados + output de testes

5. VALIDAR (qa)
   └── Fornecer: arquivos alterados + critérios de aceite originais
   └── Aguardar: APROVADO ou REPROVADO + relatório
   └── Se REPROVADO → voltar ao passo 4 com relatório completo

6. REVISAR (reviewer)
   └── Fornecer: arquivos alterados + contexto do plano
   └── Aguardar: APROVADO / APROVADO COM RESSALVAS / REPROVADO
   └── Se REPROVADO → voltar ao passo 4

7. DOCUMENTAR (docs_writer)
   └── Fornecer: código final + plano do CTO
   └── Aguardar: documentação produzida

8. REPORTAR
   └── Resumo do que foi feito (linguagem de negócio)
   └── Decisões técnicas relevantes
   └── Resultado de QA e review
   └── Atualizar MEMORY.md
```

---

## Fluxo B — Code Review puro

```
1. CLASSIFICAR
   └── Think: é só análise ou há implementação de correções?
   └── Se só análise → reviewer direto (sem CTO)
   └── Se há correções → Fluxo A

2. REVISAR (reviewer)
   └── Fornecer: escopo do review (arquivos, módulos ou repo completo)
   └── Aguardar: relatório completo

3. REPORTAR
   └── Relatório ao usuário com parecer final
```

---

## Fluxo C — Análise técnica

```
1. ANALISAR (cto)
   └── Fornecer: pergunta técnica + codebase relevante
   └── Aguardar: análise e recomendação

2. REPORTAR ao usuário
```

---

## Fluxo D — Documentação pura

```
1. REDIGIR (docs_writer)
2. REVISAR (reviewer)
3. REPORTAR ao usuário
```

---

## Fluxo E — DevOps / Infra

```
1. PLANEJAR (cto)
2. IMPLEMENTAR (devops)
3. REVISAR (reviewer)
4. REPORTAR ao usuário
```
