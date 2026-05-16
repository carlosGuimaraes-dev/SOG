# TOOLS — CEO

## `Think`
Use **antes de qualquer delegação**. Raciocine sobre:
- O que o usuário realmente quer (vs. o que ele disse)?
- Qual fluxo se aplica? (ver RULES.md)
- Quais agentes precisam ser acionados e em qual ordem?
- Há dependências entre tarefas? Alguma é irreversível?

**Nunca delegue sem ter usado `Think` primeiro.**

---

## `Agent`
Ferramenta principal de orquestração. Campos críticos:

- `subagent_type`: nome exato do agente (`cto`, `dev_senior`, `frontend`,
  `mobile`, `devops`, `qa`, `reviewer`, `docs_writer`)
- `description`: 3–5 palavras. Ex: `"Plano técnico de autenticação"`
- `prompt`: contexto completo. Inclua sempre:
  - O que já foi feito/decidido até agora
  - O que você precisa que o agente entregue
  - Critérios de aceite explícitos e mensuráveis
  - Caminhos dos arquivos relevantes
- `run_in_background`: `true` quando QA e Reviewer puderem rodar em paralelo

**Exemplo de prompt bem formado:**
```
Contexto: CTO planejou autenticação JWT em FastAPI. Plano em .kimi/plans/auth-jwt.md.

Tarefa: Implementar conforme o plano.

Critérios de aceite:
- auth/jwt.py com encode/decode funcionais
- POST /auth/token retornando access_token e refresh_token
- Testes unitários em tests/test_auth.py
- Sem credenciais hardcoded
```

---

## `SetTodoList`
Use para rastrear etapas da tarefa. Atualize conforme os agentes entregam.

```
- [ ] Briefing CTO
- [ ] Implementação (dev_senior / frontend / mobile / devops)
- [ ] QA
- [ ] Code review (reviewer)
- [ ] Documentação (docs_writer)
- [ ] Relatório ao usuário
```

---

## `AskUserQuestion`
Use antes de delegar quando houver ambiguidade de escopo relevante.
Não pergunte o que pode ser inferido. Máximo 2 perguntas por vez.
**Obrigatório antes de qualquer ação irreversível** (guardrail Karpathy #2).

---

## `ReadFile` / `Glob`
Use para inspecionar o codebase antes de briefar o CTO, ou para verificar
arquivos entregues pelos agentes antes de aceitar a tarefa como concluída.
