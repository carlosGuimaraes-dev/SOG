# Plano Técnico — Correção do Startup do Dashboard SOG

**Data:** 2026-05-16  
**Responsável:** CTO (análise)  
**Status:** Aguardando execução

---

## 1. Resumo Executivo

O stack não sobe porque **três serviços falham independentemente** e o quarto (nginx) depende deles:

| Serviço | Estado | Categoria da Falha | Arquivo(s) Envolvido(s) |
|---------|--------|-------------------|------------------------|
| `custas-api` | Restarting | **Configuração (.env)** + **Dockerfile** | `.env.api`, `api/Dockerfile`, `docker-compose.yml` |
| `custas-agente` | Restarting | **Dockerfile** (versão de dependência) | `agente/Dockerfile` |
| `custas-frontend` | Up (unhealthy) | **Dockerfile** + **docker-compose.yml** (healthcheck) | `frontend/Dockerfile`, `docker-compose.yml`, `frontend/nginx-default.conf` |
| `custas-nginx` | Created | **docker-compose.yml** (dependência) | `docker-compose.yml` (efeito colateral) |

Nenhuma ação destrutiva ou irreversível é necessária (não há deleção de dados, alteração de schema ou migração de banco).

---

## 2. Diagnóstico Detalhado

### 2.1 API — `RuntimeError: DASHBOARD_SENHA_HASH ausente ou inválido`

**Causa raiz (configuração):**
- O valor de `DASHBOARD_SENHA_HASH` em `.env.api` contém `$` não escapado:
  ```
  $2b$12$XAQoPaBNEfabrljW07OG2.5nWx8MDgiaPGum4korv7ndtYQDqg3Pa
  ```
- O Docker Compose (v2+) realiza **substituição de variáveis** ao ler arquivos `env_file`. A substring `$XAQoPaBNEfabrljW07OG2` é tratada como referência a uma variável inexistente e substituída por string vazia.
- Dentro do container, o valor real observado via `docker inspect` é:
  ```
  $2b$12.5nWx8MDgiaPGum4korv7ndtYQDqg3Pa
  ```
- A função `_hash_valido()` (`api/src/auth.py:153`) exige prefixo `$2a$`, `$2b$`, `$2x$` ou `$2y$` e comprimento mínimo de 59 caracteres. O valor truncado não atende, causando o `RuntimeError` em `app.py:36` durante o startup.

**Causa secundária (Dockerfile):**
- A imagem base `python:3.12-slim` **não possui `wget`**.
- O `api/Dockerfile` define um `HEALTHCHECK` via `wget` (linha 20), e o `docker-compose.yml` sobrescreve o healthcheck com outro `wget` (linha 60).
- Mesmo após corrigir o hash, o container seria marcado como `unhealthy` porque o comando `wget` não existe.

### 2.2 Agente — `Failed to fork exec: no such file or directory`

**Causa raiz (Dockerfile — versão de dependência):**
- O `agente/Dockerfile` instala **supercronic v0.2.33** (linha 19).
- Essa versão possui um bug conhecido ([aptible/supercronic#177](https://github.com/aptible/supercronic/issues/177)): quando executada como **PID 1**, a rotina de reaping de processos zumbis utiliza `os.Args[0]` (nome simples, sem caminho absoluto) em uma chamada `syscall.ForkExec`. Como o binário está em `/usr/local/bin/supercronic` e o CWD não é `/usr/local/bin/`, o kernel retorna `ENOENT` ("no such file or directory").
- O container é configurado como `read_only: true` e `cap_drop: ALL`, mas o bug **reproduz-se mesmo sem essas restrições** — é um defeito da versão do binário, não de permissão.

### 2.3 Frontend — `unhealthy` (nginx rodando, mas healthcheck falha)

**Causa raiz (Dockerfile + docker-compose — healthcheck):**
- O `frontend/nginx-default.conf` configura `listen 8080;` (IPv4 apenas).
- O entrypoint do container `nginx:alpine` tenta adicionar `listen [::]:8080` via script `10-listen-on-ipv6-by-default.sh`, mas falha silenciosamente porque o container é `read_only`.
- O healthcheck (tanto no `frontend/Dockerfile` linha 20 quanto no `docker-compose.yml` linha 90) usa `wget` contra `http://localhost:8080/`.
- O `wget` do busybox (Alpine) resolve `localhost` para `::1` (IPv6) primeiro; como o nginx não escuta IPv6, a conexão é recusada e o healthcheck falha.
- Verificação prática: `wget` para `127.0.0.1:8080` funciona e retorna `index.html`. O serviço está funcional, mas o healthcheck está quebrado.

### 2.4 Nginx — `Created` (não inicia)

**Causa (docker-compose — dependência):**
- O serviço `nginx` declara:
  ```yaml
  depends_on:
    api:
      condition: service_healthy
    frontend:
      condition: service_healthy
  ```
- Como `api` e `frontend` nunca atingem `healthy`, o nginx permanece no estado `Created` aguardando. É um **efeito colateral**, não uma falha primária.

---

## 3. Ações Corretivas

### Ordem de Aplicação

1. **Corrigir configuração** (`.env.api`) — não exige rebuild.
2. **Corrigir healthchecks** (`docker-compose.yml`) — não exige rebuild, efetivo imediatamente no próximo `up`.
3. **Corrigir Dockerfiles** (agente, frontend, API) — exigem `docker compose build`.
4. **Reconstruir e subir o stack**.
5. **Validar**.

### 3.1 API — Correção do Hash e do Healthcheck

#### Ação 3.1.1: Escapar `$` em `.env.api`
No arquivo `.env.api`, alterar a linha:
```bash
# Antes (interpolado pelo Docker Compose)
DASHBOARD_SENHA_HASH=$2b$12$XAQoPaBNEfabrljW07OG2.5nWx8MDgiaPGum4korv7ndtYQDqg3Pa

# Depois ($ escapado como $$)
DASHBOARD_SENHA_HASH=$$2b$$12$$XAQoPaBNEfabrljW07OG2.5nWx8MDgiaPGum4korv7ndtYQDqg3Pa
```

> **Nota:** auditar outras variáveis em `.env.api` e `.env.agente` que contenham `$`. Se houver mais ocorrências, aplicar a mesma regra de escaping (`$$`).

#### Ação 3.1.2: Substituir healthcheck `wget` por `python` (zero dependências extras)
Em `docker-compose.yml`, alterar o healthcheck do serviço `api`:
```yaml
# Antes
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]

# Depois
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
```

Em `api/Dockerfile`, atualizar o `HEALTHCHECK` embutido (boa prática, embora o compose o sobrescreva):
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

### 3.2 Agente — Correção do supercronic

#### Opção A (definitiva — recomendada): Atualizar supercronic
Em `agente/Dockerfile`, atualizar o `ARG` para a versão corrigida:
```dockerfile
ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.43/supercronic-linux-amd64
ARG SUPERCRONIC_SHA1SUM=f97b92132b61a8f827c3faf67106dc0e4467ccf2
```

#### Opção B (workaround imediato — sem rebuild)
Em `docker-compose.yml`, adicionar ao serviço `agente`:
```yaml
agente:
  init: true
```
Isso faz o Docker injetar um init system (`tini`) como PID 1, contornando o bug do supercronic v0.2.33. Recomenda-se aplicar a **Opção A** em seguida para eliminar a dívida técnica.

### 3.3 Frontend — Correção do Healthcheck

#### Ação 3.3.1: Usar `127.0.0.1` em vez de `localhost`
Em `docker-compose.yml`, alterar o healthcheck do serviço `frontend`:
```yaml
# Antes
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/"]

# Depois
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1:8080/"]
```

Em `frontend/Dockerfile`, atualizar o `HEALTHCHECK` embutido:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/ || exit 1
```

> **Alternativa (mais completa):** adicionar `listen [::]:8080;` em `frontend/nginx-default.conf`. Isso elimina a necessidade de trocar `localhost` por `127.0.0.1`, mas exige rebuild. A troca para `127.0.0.1` é a correção mínima.

### 3.4 Nginx — Nenhuma ação direta necessária
Após as correções acima, o `custas-nginx` subirá automaticamente assim que `api` e `frontend` transitarem para `healthy`.

---

## 4. Critérios de Aceite para "Dashboard Subindo"

1. **Todos os containers em `Up (healthy)`:**
   ```bash
   docker compose ps
   # Esperado: api, agente, frontend, nginx — todos healthy
   ```
2. **API respondendo:**
   ```bash
   curl -s http://localhost/api/v1/health | jq .
   # Esperado: {"status":"ok","version":"1.1.0","database":"ok"}
   ```
3. **Frontend servindo SPA:**
   ```bash
   curl -s http://localhost/ | grep -q "Custas TJDFT"
   ```
4. **Agente sem erros de fork:**
   ```bash
   docker logs custas-agente --tail 5
   # Esperado: "read crontab: /app/crontab" (sem fatal error)
   ```
5. **Nginx proxy funcionando:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost/
   # Esperado: 200
   ```

---

## 5. Riscos e Ações Irreversíveis

| Ação | Reversível? | Risco |
|------|-------------|-------|
| Editar `.env.api` | ✅ Sim (backup manual ou git se não estiver em `.gitignore`) | Baixo — apenas escaping de caracteres. |
| Alterar `docker-compose.yml` | ✅ Sim | Baixo — mudanças de healthcheck e `init: true`. |
| Alterar Dockerfiles | ✅ Sim (rebuild gera nova camada; imagem antiga preservada) | Baixo — instalação de binário já verificado por checksum. |
| Rebuild do stack | ✅ Sim (`docker compose down` + `up` sem volume remove nada) | **Médio** — garantir que o volume `./dados` não seja acidentalmente destruído. O volume é bind mount, portanto persistido no host. |

**Não há ações irreversíveis** (deleção de dados, alteração de schema, migração de banco ou mudança de senhas em produção).

---

## 6. Checklist de Execução

- [ ] 3.1.1 — Escapar `$$` em `DASHBOARD_SENHA_HASH` no `.env.api`.
- [ ] 3.1.1 — Auditar `.env.api` e `.env.agente` por outros `$` não escapados.
- [ ] 3.1.2 — Substituir healthcheck `wget` → `python` no `docker-compose.yml` (serviço `api`).
- [ ] 3.1.2 — Substituir healthcheck `wget` → `python` no `api/Dockerfile`.
- [ ] 3.2 — Atualizar `SUPERCRONIC_URL` e `SUPERCRONIC_SHA1SUM` no `agente/Dockerfile` para v0.2.43.
- [ ] 3.3.1 — Trocar `localhost` por `127.0.0.1` no healthcheck do `docker-compose.yml` (serviço `frontend`).
- [ ] 3.3.1 — Trocar `localhost` por `127.0.0.1` no `HEALTHCHECK` do `frontend/Dockerfile`.
- [ ] 3.2 (workaround) — Adicionar `init: true` no serviço `agente` do `docker-compose.yml` (opcional, caso o rebuild demore).
- [ ] Executar `docker compose down` (ou `stop`) e `docker compose up --build -d`.
- [ ] Validar com critérios de aceite (Seção 4).
