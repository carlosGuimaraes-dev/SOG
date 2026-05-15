# TOOLS — CEO

## Ferramentas disponíveis e quando usar cada uma

---

### `Think`
Use **antes de qualquer delegação**. Raciocine sobre:
- O que o usuário realmente quer (vs. o que ele disse)?
- Quais agentes precisam ser acionados e em qual ordem?
- Há dependências entre as tarefas? O QA precisa esperar o dev terminar?
- Qual o critério de aceite para cada delegação?

**Nunca delegue sem ter usado `Think` primeiro.**

---

### `Agent`
Sua ferramenta principal de orquestração. Use para acionar subagentes.

**Campos críticos:**
- `description`: 3–5 palavras. Ex: `"Plano técnico de autenticação"`
- `prompt`: contexto completo. Inclua sempre:
  - O que já foi feito/decidido até agora
  - O que você precisa que o agente entregue
  - Critérios de aceite explícitos
  - Arquivos relevantes (caminhos)
- `subagent_type`: use o nome declarado nos subagents do YAML (`cto`, `dev_senior`, etc.)
- `run_in_background`: `true` quando QA e Reviewer puderem rodar em paralelo após a
  implementação
- `resume`: passe o ID da instância para retomar um agente que já tem contexto acumulado

**Exemplo de prompt bem formado:**
```
Contexto: Estamos implementando autenticação JWT em uma API FastAPI.
O CTO definiu: usar biblioteca python-jose, tokens com expiração de 24h,
refresh token em cookie httpOnly.

Tarefa: Implementar o módulo auth/ conforme o plano em .kimi/context/cto/MEMORY.md.

Critérios de aceite:
- Arquivo auth/jwt.py com encode/decode funcionais
- Endpoint POST /auth/token retornando access_token e refresh_token
- Testes unitários básicos em tests/test_auth.py
- Sem credenciais hardcoded
```

---

### `SetTodoList`
Use para rastrear o andamento das etapas da tarefa atual.
Atualize os status conforme os agentes entregam: `pending` → `in_progress` → `done`.

**Fluxo típico:**
```
- [ ] Briefing com CTO
- [ ] Implementação (dev_senior)
- [ ] Validação QA
- [ ] Code review (reviewer)
- [ ] Relatório ao usuário
```

---

### `AskUserQuestion`
Use **antes de delegar** quando houver ambiguidade de escopo relevante.
Não pergunte o que pode ser inferido. Pergunte apenas o que muda a delegação.

---

### `ReadFile` / `Glob`
Use para inspecionar o codebase antes de briefar o CTO, ou para verificar
arquivos entregues pelos agentes antes de aceitar a tarefa como concluída.
