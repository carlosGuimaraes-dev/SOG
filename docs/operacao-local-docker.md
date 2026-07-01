# Operacao local em Docker

Este documento registra a arquitetura alvo atual do SOG.

## Decisao atual

O sistema deve rodar localmente com todos os componentes em Docker Compose:

- `nginx`
- `frontend`
- `api`
- `agente`

O projeto nao deve depender de VPS, cron do host, Python/Node instalados no host
para operacao normal, nem execucao manual recorrente do agente fora do Compose.

## Agente

O agente deve ser um processo longo dentro do container, sem cron. O container
permanece ativo aguardando comandos do dashboard via SQLite.

Fluxo esperado:

1. O usuario acessa o dashboard.
2. O usuario clica em `Iniciar Agente`.
3. A API grava `comando='iniciar'` em `agente_controle`.
4. O agente, ja em execucao no container, le o comando.
5. O agente abre um navegador interativo dentro do ambiente containerizado.
6. O usuario faz login SSO/2FA no PJe e no SISTJWEB.
7. O agente salva `storage_state` em volume persistente.
8. O agente executa o ciclo de trabalho: coleta, preenche, acompanha aprovados,
   emite e anexa.

## Navegador interativo

Como o agente roda em Docker, o navegador do fluxo SSO/2FA deve ser exposto de
forma containerizada. A abordagem preferida e uma interface de browser remoto
do proprio container, por exemplo noVNC ou mecanismo equivalente.

O usuario usa o navegador local apenas para acessar essa interface. O Chromium,
cookies, sessoes e `storage_state` ficam isolados no container/volume Docker.

Nao usar login programatico com usuario/senha de PJe/SISTJWEB. Essas credenciais
nao devem existir em arquivos `.env`.

## Persistencia

O Compose deve persistir:

- banco SQLite em `./dados`
- screenshots e demonstrativos em `./dados`
- `storage_state` do PJe/SISTJWEB em volume Docker ou subdiretorio persistente
  controlado pelo Compose

## Bootstrap operacional

Antes do primeiro `docker compose up`, preparar o runtime local com:

```bash
./scripts/prepare-runtime.sh
```

Quando o host ainda nao tiver Node.js, npm, Docker CLI ou WSL, usar tambem:

```bash
python3 ./scripts/prepare-internal-runtime.py
```

Para subir com verificação e mensagem de suporte em caso de falha:

```bash
./scripts/start-local.sh
```

Quando o preparo rodar sem terminal interativo, a autorização para instruções
manuais deve ser explícita:

```bash
SOG_RUNTIME_PREP_AUTHORIZATION=approved ./scripts/start-local.sh
```

Esse bootstrap:

- cria `.env.api` e `.env.agente` a partir de `.env.example` sem sobrescrever
  arquivos existentes
- cria `./dados`, `./dados/auth`, `./dados/screenshots` e
  `./dados/demonstrativos`
- deixa o caminho de `storage_state` persistente em `/dados/auth`
- grava `dados/support/runtime-diagnostic.json` com detalhes técnicos
  sanitizados para o suporte
- roda um preflight antes do `docker compose up` e só exige containers ativos
  depois da tentativa de subida
- grava `dados/support/runtime-preparation-state.json` quando o preparo do host
  depender de autorizacao do operador ou de retomada apos reboot

O fluxo HITL de preparo interno:

- registra dependencias ausentes do host
- solicita autorizacao explicita antes de continuar
- aponta somente para fontes oficiais de Node.js/npm, Docker e WSL
- explica a elevacao antes de qualquer etapa de UAC do WSL
- persiste estado suficiente para retomar apos reinicializacao

## Fora de escopo

- Rodar o agente no host nativo.
- Rodar o agente por cron.
- Rodar em VPS.
- Abrir o Chrome instalado no host via CDP como mecanismo principal.
