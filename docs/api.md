# API do dashboard

Base path: `/api/v1`

## Autenticação

- `POST /auth/login`: valida usuário e senha, emite cookies `httpOnly`
- `POST /auth/refresh`: rota o refresh token e reemite o par de cookies
- `GET /auth/me`: retorna o usuário autenticado
- `POST /auth/logout`: revoga o refresh token corrente e limpa os cookies

O frontend usa `withCredentials: true` e não lê tokens do `localStorage`.

## Saúde

- `GET /health`: health check público com status da API e do SQLite

## Processos

- `GET /processos`: retorna duas listas
  - `aguardando_aprovacao`
  - `pendente_manual`
- `GET /processos/{processo_id}`: detalhe do processo, dados do processo, logs e documentos
- `GET /processos/{processo_id}/screenshot`: retorna screenshot autenticado do processo
- `POST /processos/{processo_id}/reprocessar`: solicita reprocessamento para status elegíveis

`GET /processos` aceita `limit` e `offset`.

## Aprovação operacional

- `POST /aprovar/{processo_id}`: só aceita processos em `aguardando_aprovacao`
- `POST /rejeitar/{processo_id}`: idem, com observação do operador

As rotas usam transação SQLite com `BEGIN IMMEDIATE` antes de alterar status.

## Agente e ciclos

- `POST /agente/iniciar`
- `POST /agente/parar`
- `GET /agente/status`
- `GET /agente/ciclos/atual`
- `GET /agente/ciclos/ultimo`
- `GET /agente/ciclos/{ciclo_uuid}`

Estados relevantes do agente observados no código:

- `parado`
- `iniciando`
- `autenticando`
- `executando`
- `dormindo`
- `aguardando_login`
- `parando`
- `pausado`
- `interrompido`
- `erro`
- `erro_pausado`

## Tarefas assíncronas

- `POST /tarefas`
- `GET /tarefas`
- `GET /tarefas/{task_id}`
- `POST /tarefas/{task_id}/cancelar`

Tipos aceitos no código:

- `consultar_etiqueta_pje`
- `consultar_documentos_pje`
- `baixar_pdf_pje`
- `verificar_sessao_pje`
- `reautenticar_pje`
- `preencher_sistj`
- `gravar_aprovar_sistj`
- `verificar_sessao_sistj`
- `reautenticar_sistj`
- `anexar_demonstrativo_pje`
- `reprocessar_processo`

## Dashboard agregado

- `GET /dashboard/sessoes`: resume saúde do agente, estado de sessão PJe/SISTJ e contagem de tarefas

## Status de processo documentados no código

Os docs atuais e os componentes usam ao menos estes status:

- `pendente`
- `aguardando_aprovacao`
- `aprovado`
- `rejeitado`
- `emitido`
- `erro`
- `pendente_manual`

Outros estados podem existir em migrações, testes ou fluxos auxiliares, mas os
acima são os confirmados no contrato principal desta auditoria.
