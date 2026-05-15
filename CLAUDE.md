# Pipeline de Custas Processuais TJDFT

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
