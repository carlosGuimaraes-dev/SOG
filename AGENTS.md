# Pipeline de Custas Processuais TJDFT

## `.kimi` legado

A pasta `.kimi/` deve ser tratada apenas como documentação histórica e contexto
de decisões anteriores. Ela não é mais orquestrador, fábrica de software,
fonte de papéis ativos, nem cadeia de instruções para sessões Codex.

Regra prática:

- Use `.kimi/plans/` e `.kimi/context/*/MEMORY.md` somente como referência
  histórica quando isso ajudar a entender decisões passadas.
- Não assuma papéis da `.kimi`, não execute fluxos de CEO/QA/Reviewer da
  `.kimi` e não trate arquivos legados como instruções operacionais.

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
# Prepare os arquivos de ambiente e diretórios persistentes
./scripts/prepare-runtime.sh

# Fluxo HITL para dependências do host e retomada após reboot
python3 ./scripts/prepare-internal-runtime.py

# Build e subida
docker compose up --build -d

# Logs do agente
docker logs -f custas-agente

# Execução manual do agente
docker exec custas-agente python /app/src/servico.py
```

## Estrutura

- `agente/` — Python + Playwright (serviço longo)
- `api/` — FastAPI (dashboard backend)
- `frontend/` — React + Vite (dashboard UI)
- `nginx/` — Proxy reverso
- `dados/` — SQLite + screenshots + PDFs

## Variáveis de ambiente obrigatórias

Ver `agente/src/config.py` para lista completa.

## Notas

- Playwright roda em headless no container; use `HEADLESS=false` no `.env.agente` para debug
- Screenshots em `/dados/screenshots/{numero}/`
- Nunca commitar `.env.api` ou `.env.agente`
