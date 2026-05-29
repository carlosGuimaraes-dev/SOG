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

## Fora de escopo

- Rodar o agente no host nativo.
- Rodar o agente por cron.
- Rodar em VPS.
- Abrir o Chrome instalado no host via CDP como mecanismo principal.
