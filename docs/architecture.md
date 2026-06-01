# Arquitetura do SOG

## Componentes

### `agente/`

- Automação Python 3.12 com Playwright para PJe e SISTJWEB.
- Serviço longo implementado em `agente/src/servico.py`.
- Notificações operacionais por Telegram em `agente/src/utils/telegram.py`.
- Execução assíncrona de tarefas específicas em `agente/src/modulos/executor_tarefas.py`.

### `api/`

- Backend FastAPI servido sob `/api/v1`.
- Usa `sog_shared.db` para acessar o SQLite compartilhado.
- Expõe autenticação, fila de processos, histórico, controle do agente, ciclos,
  tarefas e estado agregado do dashboard.

### `frontend/`

- Dashboard React com rotas protegidas para:
  - ciclo atual (`/`)
  - fila de processos (`/processos`)
  - detalhe (`/detalhe/:id`)
  - histórico (`/historico`)
- A barra de status do agente consome `/agente/status`, `/agente/ciclos/atual`,
  `/agente/ciclos/ultimo` e `/dashboard/sessoes`.

### `shared/`

- Pacote Python compartilhado com schema SQLite, conexões, PRAGMAs e helpers de domínio.
- Concentra o contrato entre agente e API para evitar cópia cruzada de código.

### `nginx/`

- Entrada HTTP do Compose principal.
- Encaminha frontend e API para uso local.

## Fluxo operacional

1. O dashboard autentica o operador via `/auth/login`.
2. A API emite cookies `access_token` e `refresh_token` `httpOnly`.
3. O operador inicia ou retoma um ciclo do agente via `/agente/iniciar`.
4. A API grava o comando em `agente_controle`.
5. O agente lê o controle, autentica sessões e executa:
   - coleta de processos
   - tarefas assíncronas
   - preenchimento e emissão
   - atualização de logs e status
6. O operador aprova, rejeita ou solicita reprocessamento pelo dashboard.

## Persistência

O Compose principal compartilha `./dados` entre `agente` e `api`. O SQLite é
aberto com:

- `PRAGMA journal_mode=WAL`
- `PRAGMA busy_timeout=5000`

Tabelas operacionais relevantes:

- `processos`
- `dados_processo`
- `documentos_pje`
- `log_execucao`
- `agente_controle`
- `agente_ciclos`
- `agente_ciclo_membros`
- `tarefas`

## Estado atual do agente no Docker

O código já contém um serviço longo com máquina de estados, mas a imagem
empacotada ainda usa:

- `supercronic`
- `agente/crontab`

Isso significa que a arquitetura desejada e a forma de bootstrap do container
ainda não estão totalmente alinhadas.

## Sessões e `storage_state`

O código do agente usa `AuthManager` com arquivos de `storage_state` derivados de:

- `STORAGE_STATE_DIR`
- `STORAGE_STATE_PJE`
- `STORAGE_STATE_SISTJ`

O caminho default vem de `Path.home() / ".sog" / "auth"` no container. O Compose
atual não documenta um volume dedicado para esse diretório, então a persistência
dessas sessões entre rebuilds deve ser tratada como ponto de validação, não como
garantia documentada.
