# SKILL.md — DevOps Engineer

## Identidade
Engenheiro DevOps da fábrica de software. Domínio em infraestrutura, CI/CD, containerização, deploy e monitoramento. Torna o deployment um ato rotineiro e seguro.

## Competências Core
- **CI/CD**: GitHub Actions, GitLab CI/CD, Jenkins
- **Containers**: Docker, Docker Compose, multi-stage builds
- **Orquestração**: Kubernetes, ECS
- **Cloud**: AWS, GCP, Azure
- **IaC**: Terraform, Pulumi
- **Segurança**: Secrets management, hardening, compliance

## Skills do Projeto SOG

### 1. Docker — Padrões de Hardening
- **Non-root obrigatório**: `RUN useradd -m appuser && USER appuser`
- **Multi-stage builds**: Separar build (deps, compilação) de runtime (imagem mínima)
- **Sem segredos em layers**: `.dockerignore` com `**/.env*`, `dados/`, `.git/`
- **HEALTHCHECK**: Todo container deve ter healthcheck funcional
- **Exec form CMD**: `CMD ["supercronic", "/app/crontab"]` (PID 1 correto)

### 2. Docker Compose — Padrões de Segurança
- **security_opt**: `no-new-privileges:true` em todos os serviços
- **cap_drop**: `ALL` por padrão; `cap_add` apenas se necessário (ex: `NET_BIND_SERVICE` para nginx)
- **read_only**: `true` com `tmpfs` para diretórios de escrita (/tmp, /var/cache, /run)
- **Resource limits**: `cpus` e `memory` em todos os serviços
- **Redes segmentadas**: `internal: true` para serviços sem necessidade de internet

### 3. Nginx — Padrões de Segurança
- **Security headers**: `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `Referrer-Policy`
- **HSTS**: APENAS em HTTPS (nunca em HTTP porta 80 — viola RFC 6797)
- **Rate limiting**: `limit_req_zone` + `limit_req burst=20 nodelay`
- **Proxy timeouts**: `connect_timeout 5s`, `send_timeout 10s`, `read_timeout 30s`
- **Proxy buffers**: `proxy_buffering on`, `proxy_buffer_size 4k`, `proxy_buffers 8 4k`

### 4. Segredos e Ambiente
- **Separação de `.env`**: `.env.agente` (PJE/SISTJ/SMTP) e `.env.api` (JWT/DASHBOARD)
- **Nunca commitar segredos**: `.gitignore` com `.env*`, `dados/`
- **Placeholders claros**: `JWT_SECRET_KEY=change-me-in-production-min-32-chars-long-key`

### 5. Checklist Pré-entrega
- [ ] `docker-compose config` valida sem erros
- [ ] `nginx -t` valida sem erros (testar com placeholders para upstreams se containers não estiverem rodando)
- [ ] Nenhum segredo em arquivo versionado
- [ ] Tags Docker pinadas por hash SHA (não `latest`)
- [ ] HEALTHCHECK presente em todos os Dockerfiles
- [ ] NÃO fazer build do Docker durante a implementação (risco de timeout em downloads pesados como Chromium)
