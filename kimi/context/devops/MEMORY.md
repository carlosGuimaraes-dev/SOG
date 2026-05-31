# MEMORY — DevOps Engineer

> Arquivo dinâmico. Registre plataforma, pipelines, secrets e procedimentos.

---

## Plataforma de CI/CD

<!-- GitHub Actions / GitLab CI / outro -->
_Não identificada ainda._

---

## Repositório e branches

<!-- Organização de branches, branch protection rules, política de PR.
Ex: main (protegida, requer PR + CI verde + 1 aprovação)
    develop (integração), feature/* (desenvolvimento)
-->
_Não documentado ainda._

---

## Pipelines existentes

<!-- Nome, arquivo, propósito e status de cada pipeline.
Ex: .github/workflows/ci.yml — lint + test em PRs (ativo)
    .github/workflows/deploy.yml — deploy em prod via tag (ativo)
-->
_Nenhum mapeado ainda._

---

## Secrets configurados

<!-- Nomes dos secrets (nunca os valores) e onde estão configurados.
Ex: AWS_ACCESS_KEY_ID — GitHub Secrets (repo level)
    DATABASE_URL — GitLab CI Variables (masked, protected)
-->
_Nenhum registrado ainda._

---

## Ambientes

<!-- Staging, produção, desenvolvimento e suas configurações.
Ex: staging: ECS cluster us-east-1, deploy automático em merge para develop
    production: ECS cluster us-east-1, deploy manual via tag vX.Y.Z
-->
_Nenhum ambiente documentado ainda._

---

## Procedimentos de deploy e rollback

### Deploy (atual — Docker Compose local)
```bash
# Produção
docker-compose up -d --build

# Desenvolvimento
docker-compose -f docker-compose.dev.yml up -d --build
```

### Rollback (Wave 7)
```bash
# Reverter artefatos de infra para versão anterior
git checkout HEAD~1 -- agente/Dockerfile agente/requirements.txt agente/requirements-dev.txt \
  agente/crontab frontend/Dockerfile docker-compose.yml docker-compose.dev.yml \
  nginx/nginx.conf nginx/nginx-dev.conf

# Rebuild e restart
docker-compose down
docker-compose up -d --build
```

### Rollback de emergência (apenas imagens Docker)
```bash
docker-compose down
docker images | grep custas
# docker tag <imagem-anterior> <imagem-atual>
docker-compose up -d
```

---

## Gotchas de infra identificados

- **frontend/Dockerfile multi-stage + non-root:** O stage final usa `nginx:alpine`. Para rodar como `appuser` (non-root), foi necessário:
  - Trocar `useradd` (Debian) por `adduser -D` (Alpine)
  - Mudar a porta do nginx de 80 → 8080 (portas <1024 requerem root)
  - Atualizar `proxy_pass` no `nginx/nginx.conf` de `frontend:80` → `frontend:8080`
  - Ajustar healthcheck do serviço `frontend` no docker-compose.yml para porta 8080
  - Dar chown nos diretórios necessários: `/usr/share/nginx/html`, `/etc/nginx/conf.d`, `/var/cache/nginx`, `/var/log/nginx`
- **Segurança de env files:** O `.env` único foi separado em `.env.agente` (PJE/SISTJ/SMTP/Datajud/Playwright) e `.env.api` (Dashboard/JWT/CORS/DB). Ambos ainda compartilham `DB_PATH`. `.env.api` foi completado com `JWT_SECRET_KEY` (≥32 chars) e `FRONTEND_URL` para CORS. `.env.agente` documenta `PJE_INDICADORES_SUCESSO` como comentário.
- **Nginx proxy /api/ → /api/v1/:** O location `/api/` no nginx foi ajustado para fazer `proxy_pass http://api:8000/api/v1/;`. Isso requer que o backend registre routers com `prefix="/api/v1"` (ou use `root_path="/api/v1"` no FastAPI, já que o path completo `/api/v1/...` é repassado). O frontend atual ainda chama `/api/...`; o nginx faz o rewrite transparente.
- **Redirect HTTP→HTTPS:** Adicionado como comentário nos nginx.conf. Quando SSL for configurado, descomentar o bloco `server { listen 80; return 301 https://$host$request_uri; }`.
- **Agente Dockerfile reconciliação Wave 6 + Wave 7:** A Wave 6 adicionou `COPY shared/ ./shared/` e `pip install -e ./shared` ao agente/Dockerfile. A Wave 7 precisou reescrever o Dockerfile com multi-stage build, non-root, supercronic, etc., mantendo o shared package. O Dockerfile final tem duas stages: builder (instala deps + shared + playwright chromium) e runtime (copia venv, browsers, código, crontab; cria appuser; instala supercronic).
- **Playwright + read_only containers:** O agente precisa de `tmpfs: [/tmp]` porque o Playwright escreve arquivos temporários durante a automação. O diretório final `/dados/screenshots` é um volume bind mount e continua funcionando com `read_only: true`.
- **Nginx cap_add NET_BIND_SERVICE:** Com `cap_drop: ALL`, o nginx não consegue fazer bind na porta 80 (privilegiada). Foi necessário adicionar `cap_add: [NET_BIND_SERVICE]` apenas no serviço nginx.
- **Build do agente é lento:** O step `playwright install chromium` baixa ~157MB e extrai. O build completo ultrapassa 5 minutos. Recomenda-se buildar com cache ou em CI com timeout generoso.

---

## Débitos de infra identificados

- **Build do agente não testado até o fim:** Timeout do agente impede validação do tamanho da imagem (< 800MB) e do funcionamento como non-root. Build manual necessário.
- **TLS interno entre containers:** Planejado para Wave 8 ou pós-MVP. Rede `sog-internal` com `internal: true` isola api/frontend, mas a comunicação ainda é em plaintext.

---

## Histórico de mudanças de infra

### 2026-05-15 — Wave 7: Infra Hardening Completo

Issue | Arquivo(s) | Mudança
--- | --- | ---
CR-009 / HI-010 / M-050 | `agente/Dockerfile` | Multi-stage build; non-root (`appuser`); `supercronic` (PID 1, exec form); `HEALTHCHECK` em Python puro verificando supercronic; `chmod 0600` no crontab
M-036 | `agente/Dockerfile` | Multi-stage build copiando apenas venv + browsers; deps de sistema reduzidas ao mínimo para Chromium headless; removidos drivers macOS/Windows do Playwright
M-037 | `frontend/Dockerfile` | Copia `package-lock.json` + `npm ci` (build determinístico)
M-038 | `agente/requirements.txt`, `agente/requirements-dev.txt` (novo) | `pytest`/`pytest-mock` removidos de produção; criado `requirements-dev.txt`
M-040 / M-041 | `docker-compose.yml`, `docker-compose.dev.yml` | Adicionados `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]`, `cap_add: [NET_BIND_SERVICE]` (nginx apenas), `read_only: true`, `tmpfs`, `deploy.resources.limits` (cpus/memory)
M-042 | `agente/Dockerfile`, `agente/crontab` | `chmod 0600` no crontab; crontab sem redirecionamento para `/var/log` (read-only fs)
M-044 | `docker-compose.yml`, `docker-compose.dev.yml` | Redes segmentadas: `sog-internal` (`internal: true`) para api/frontend; `sog-external` para nginx; agente usa rede default (necessita internet)
M-045 / INF-001 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | Proxy timeouts (`connect` 5s, `send` 10s, `read` 30s), buffering (`4k/8x4k`); rate limiting nativo (`limit_req_zone` 10r/s, burst 20)
M-053 | `.gitignore` | Já cobria `.env*`, `dados/`, `node_modules/`, `__pycache__`; nenhuma mudança necessária
— | `docker-compose.yml` | Imagem `nginx:alpine` pinada por digest SHA (`sha256:dc48b7a872a79fb541ba5081d320b11b549231bc63ba465a7495afaa7d2ebcb8`)

### 2026-05-15 — Wave 1: Segurança Crítica I (Infra)

Issue | Arquivo(s) | Mudança
--- | --- | ---
CR-015 | `.dockerignore` (novo) | Criado com exclusões de `.env*`, `dados/`, `.git`, `node_modules`, `__pycache__`, etc.
CR-007 | `docker-compose.yml`, `docker-compose.dev.yml` | Removido `ports: - "8000:8000"` do serviço `api`. API não mais exposta diretamente no host.
HI-011 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | Adicionados 5 security headers: X-Frame-Options, X-Content-Type-Options, CSP, HSTS, Referrer-Policy.
HI-010 | `api/Dockerfile`, `frontend/Dockerfile` | Containers rodam como non-root (`appuser`). API usa `useradd`; frontend (Alpine) usa `adduser -D` + ajuste de porta 80→8080.
M-039 | `docker-compose.yml` | Healthcheck do nginx corrigido de `/health` (inexistente) para `/`.
M-050 | `api/Dockerfile`, `frontend/Dockerfile` | Adicionados HEALTHCHECKs com `wget` nas portas corretas.
M-052 | `frontend/package.json` | Adicionados scripts `test`, `test:watch`, `lint`.
HI-015 / M-043 | `docker-compose.yml`, `.env.agente` (novo), `.env.api` (novo) | Separados env files por serviço. Agente usa `.env.agente`; API usa `.env.api`.
2026-05-15 — Wave 1 QA Fix | `.env.api`, `.env.agente`, `.env.example` | Completado `.env.api` com `JWT_SECRET_KEY` e `FRONTEND_URL`. Adicionado comentário `PJE_INDICADORES_SUCESSO` em `.env.agente`. `.env.example` reescrito para refletir a separação `.env.api` / `.env.agente`.

### 2026-05-15 — Wave 3: Auth Cross-Cutting (Infra)

Issue | Arquivo(s) | Mudança
--- | --- | ---
M-007 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | Adicionado bloco comentado para redirect HTTP→HTTPS (`return 301 https://$host$request_uri;`). Ativar quando `SSL_ENABLED=true`.
HI-015 / M-043 | `docker-compose.dev.yml` | Serviço `api`: `env_file` alterado de `.env` para `.env.api`.
CR-005 | `docker-compose.yml`, `docker-compose.dev.yml` | Removido volume `./dados/screenshots:/usr/share/nginx/html/screenshots:ro` do serviço `nginx`. Screenshots não mais servidos diretamente pelo nginx.
CR-005 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | Verificado: não existia `location /screenshots/` nos arquivos de configuração. Nenhuma remoção necessária.
M-008 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | `location /api/` ajustado para `proxy_pass http://api:8000/api/v1/;`. O frontend chama `/api/...` e o nginx repassa como `/api/v1/...` para o backend.

### 2026-05-15 — Wave 7: Infra Hardening Completo

Issue | Arquivo(s) | Mudança
--- | --- | ---
CR-009 / HI-010 / M-050 | `agente/Dockerfile` | Reescrito com multi-stage build. Stage runtime: `useradd -m appuser`, `USER appuser`, supercronic v0.2.33 (binário estático, hash SHA1 verificado), `CMD ["supercronic", "/app/crontab"]` (exec form, PID 1), `HEALTHCHECK` via `pgrep -x supercronic`.
M-036 | `agente/Dockerfile` | Multi-stage build: stage 1 instala deps + shared + playwright chromium; stage 2 copia apenas venv e browsers. Meta: < 800MB (build não completado por timeout; validação pendente).
M-037 | `frontend/Dockerfile` | `COPY frontend/package.json frontend/package-lock.json ./` + `RUN npm ci` para cache determinístico.
M-038 | `agente/requirements.txt`, `agente/requirements-dev.txt` (novo) | Removidos `pytest` e `pytest-mock` de `requirements.txt`. Criado `requirements-dev.txt` com as mesmas deps + pytest.
M-040 / M-041 | `docker-compose.yml` | Adicionados `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]` (nginx tem `cap_add: [NET_BIND_SERVICE]`), `read_only: true`, `tmpfs` por serviço, `deploy.resources.limits` (cpus/memory) ajustados por serviço.
M-042 | `agente/Dockerfile`, `agente/crontab` | Crontab copiado para `/app/crontab` com `chmod 0600` (não 0644). Redirecionamento `/var/log` removido do crontab (read-only fs).
M-044 | `docker-compose.yml`, `docker-compose.dev.yml` | Redes `sog-external` (bridge) e `sog-internal` (bridge, `internal: true`). api/frontend isolados em `sog-internal` (sem internet). nginx em ambas. agente em rede padrão (precisa de internet para PJe/Datajud/SMTP).
M-045 / INF-001 | `nginx/nginx.conf`, `nginx/nginx-dev.conf` | Adicionados `proxy_connect_timeout 5s`, `proxy_send_timeout 10s`, `proxy_read_timeout 30s`, `proxy_buffering on`, `proxy_buffer_size 4k`, `proxy_buffers 8 4k`. Rate limiting: `limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s` + `limit_req zone=api burst=20 nodelay` no location `/api/v1/`.
M-053 | `.gitignore` | Verificado: cobre `.env*`, `dados/`, `node_modules/`, `__pycache__`. Nenhuma alteração necessária.
