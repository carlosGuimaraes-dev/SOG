---
name: docker-compose-infra
description: >
  Use para orquestrar multi-container Docker Compose em dev/staging/prod.
  Aborda networks, volumes, health checks, non-root containers,
  multi-stage builds e override para desenvolvimento local.
---

# docker-compose-infra

Orquestração de containers com `docker-compose`.

## Quando usar

- Subir stack local de múltiplos serviços (API, frontend, nginx, banco).
- Garantir reprodutibilidade entre dev e produção.
- Centralizar configuração de networks, volumes e variáveis de ambiente.

## Padrões principais

### Multi-container setup

Separe cada serviço em um container distinto. Evite “god containers”.

```yaml
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
```

### Networks e volumes

Use networks nomeadas para comunicação inter-service. Prefira volumes nomeados.

```yaml
services:
  api:
    networks:
      - sog-net
    volumes:
      - api-data:/app/data

networks:
  sog-net:
    driver: bridge

volumes:
  api-data:
```

### Health checks

Adicione `healthcheck` para dependências que precisam estar prontas.

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

### Variáveis de ambiente

Use `.env` + `env_file`. Nunca commite secrets no `docker-compose.yml`.

```yaml
services:
  api:
    env_file:
      - .env.api
    environment:
      - APP_ENV=${APP_ENV:-development}
```

### Non-root containers

Crie usuário dedicado no Dockerfile e use no compose.

```dockerfile
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser
```

```yaml
services:
  api:
    user: "1000:1000"
```

### Multi-stage builds

Use `target` no compose para builds separados.

```yaml
services:
  api:
    build:
      context: ./api
      target: production
```

```dockerfile
FROM python:3.11-slim AS builder
# ...
FROM python:3.11-slim AS production
COPY --from=builder /app/dist .
```

### docker-compose.override.yml para dev

Coloque overrides locais (volumes bind, debug, hot-reload) no override.

```yaml
# docker-compose.override.yml
services:
  api:
    volumes:
      - ./api/src:/app/src
    command: uvicorn main:app --reload
```

### Logs e debugging

```bash
# Logs em tempo real
docker-compose logs -f api

# Últimas 50 linhas
docker-compose logs --tail=50 api

# Execução interativa
docker-compose exec api bash
```

## Anti-patterns

- Subir banco de dados em container para produção sem backup de volumes.
- Usar `depends_on` sem `condition: service_healthy` (só aguarda container iniciar, não serviço).
- Commitar `.env` com secrets.
- Expor portas desnecessárias (`ports: - "6379:6379"` do Redis para host).
