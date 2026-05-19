# Pipeline de Custas Processuais TJDFT

## Codex / `.kimi`

Este repositório também contém uma estrutura de agentes em `.kimi/`.

Quando a tarefa envolver os papéis, planos ou skills da `.kimi`, siga esta ordem:

1. Assuma o papel de **CEO da `.kimi`** como orquestrador da sessão.
2. Leia `.kimi/AGENTS.md` como ponto de entrada.
3. Depois leia o `AGENTS.md` mais próximo do subdiretório relevante, se existir.
4. Em seguida, siga os arquivos do papel correspondente em `.kimi/context/<papel>/`.
5. Use `.kimi/plans/<tarefa>.md` quando a tarefa vier acompanhada de um plano técnico.

Regra prática:

- Se o pedido for sobre o sistema `.kimi`, trate a pasta como documentação operacional do projeto e orquestre a sessão como CEO até encerrar a tarefa.
- Se o pedido for sobre implementação normal do repo, siga o `AGENTS.md` da raiz e só entre em `.kimi` quando a tarefa pedir isso ou quando houver plano/contexto referenciado lá.

## Karpathy Skills — Behavioral Guardrails

Source: <https://github.com/forrestchang/andrej-karpathy-skills>

### 1. Think Before Coding

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

- No features beyond what was asked.
- No abstractions for single-use code.
- If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused.

### 4. Goal-Driven Execution

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"

For multi-step tasks, state a brief plan:

```markdown
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

## Execução

```bash
# Preencha o .env antes de iniciar
cp .env.example .env

# Build e subida
docker-compose up --build -d

# Logs do agente
docker logs -f custas-agente

# Execução manual do agente
docker exec custas-agente python /app/src/main.py
```

## Estrutura

- `agente/` — Python + Playwright (cron horário)
- `api/` — FastAPI (dashboard backend)
- `frontend/` — React + Vite (dashboard UI)
- `nginx/` — Proxy reverso
- `dados/` — SQLite + screenshots + PDFs

## Variáveis de ambiente obrigatórias

Ver `agente/src/config.py` para lista completa.

## Notas

- Playwright roda em headless no container; use `HEADLESS=false` no .env para debug
- Screenshots em `/dados/screenshots/{numero}/`
- Nunca commitar `.env`
