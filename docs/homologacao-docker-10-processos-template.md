# Template de evidência: homologação Docker com 10 processos

Use este arquivo como modelo de coleta de evidências para homologação local do
SOG em Docker com um lote de 10 processos. O objetivo é registrar o que o
runtime atual realmente demonstrou, sem incorporar dados sensíveis no
repositório.

## Como usar

1. Copie este template para o artefato de homologação da execução.
2. Preencha datas, anexos, UUIDs de ciclo e resultados observados.
3. Anexe screenshots, PDFs e exportações fora do repositório.
4. Neste documento, referencie apenas caminhos, nomes de anexos ou IDs
   redigidos.

## Escopo comprovado por este template

- Subida do `docker-compose.yml` principal com `agente`, `api`, `frontend` e
  `nginx`
- Health da API exposto via nginx
- Inicialização do agente no runtime atual em Docker
- Execução de um ciclo com snapshot de 10 processos
- Registro de membros do ciclo e contadores agregados
- Evidência persistida de emissão quando houver processos concluídos com sucesso
- Resumo operacional por Telegram sem PII, quando a integração estiver ativa

## Limites conhecidos

- O bootstrap do container do agente ainda usa `supercronic`; não declarar neste
  template que o container publicado já roda exclusivamente o serviço longo.
- O template não homologa regras TJDFT de cálculo. Ele registra comportamento
  técnico observável do sistema.
- O repositório não documenta persistência garantida de `storage_state` entre
  rebuilds; tratar isso como item de verificação, não como premissa.

## Identificação da execução

| Campo | Preencher |
|---|---|
| Data da execução | `AAAA-MM-DD` |
| Ambiente | `localhost` / host homologado |
| Responsável técnico | |
| Operador de homologação | |
| Commit ou revisão avaliada | |
| Compose utilizado | `docker-compose.yml` |
| Total planejado no lote | `10` |
| Total efetivamente carregado no ciclo | |
| Anexos externos | |

## Pré-requisitos

Marcar apenas o que foi efetivamente validado.

| Item | Evidência | Status |
|---|---|---|
| `.env.api` preenchido | referência do arquivo usado | `[] ok [] n/a [] falha` |
| `.env.agente` preenchido | referência do arquivo usado | `[] ok [] n/a [] falha` |
| `DASHBOARD_SENHA_HASH` válido | comando ou evidência de login | `[] ok [] falha` |
| `JWT_SECRET_KEY` configurado | evidência de startup da API | `[] ok [] falha` |
| `TELEGRAM_BOT_TOKEN` configurado | evidência de startup do agente ou notificação | `[] ok [] falha` |
| `TELEGRAM_CHAT_ID` configurado | evidência de startup do agente ou notificação | `[] ok [] falha` |
| Lote de 10 processos preparado para a execução | referência externa do lote | `[] ok [] falha` |

## Evidência de subida do ambiente

### Comandos executados

```bash
docker-compose up -d --build
docker-compose ps
curl -sS http://localhost/api/v1/health
docker logs --tail 200 custas-agente
docker logs --tail 200 custas-api
```

### Registro

| Verificação | Evidência anexada | Resultado observado |
|---|---|---|
| `docker-compose up -d --build` concluiu sem erro | | |
| `docker-compose ps` mostra os 4 serviços | | |
| `GET /api/v1/health` respondeu com sucesso | | |
| API sem erro de configuração bloqueante | | |
| Agente sem falha por ausência de Telegram | | |

## Evidência de login e controle operacional

| Verificação | Evidência anexada | Resultado observado |
|---|---|---|
| Login no dashboard concluído | | |
| Dashboard exibiu status do agente | | |
| Comando de início do agente aceito | | |
| `ciclo_uuid` registrado | | |
| Sessões PJe/SISTJ verificadas no dashboard | | |

### APIs e consultas úteis

Estas consultas são opcionais e servem para consolidar a evidência coletada no
dashboard:

```bash
curl -sS http://localhost/api/v1/health

docker exec custas-api sqlite3 /dados/custas.db "
SELECT uuid, status, total_membros, total_concluidos, total_erros, criado_em, finalizado_em
FROM agente_ciclos
ORDER BY criado_em DESC
LIMIT 3;
"

docker exec custas-api sqlite3 /dados/custas.db "
SELECT ciclo_uuid, COUNT(*) AS membros
FROM agente_ciclo_membros
GROUP BY ciclo_uuid
ORDER BY MAX(criado_em) DESC
LIMIT 3;
"
```

## Lote homologado

Preencher uma linha por processo. Não anexar PII no markdown; usar referência
para anexo externo ou mascarar o número.

| Item | Processo mascarado | Origem no ciclo | Status inicial | Status final | Evidência de dashboard | Evidência de arquivo/PDF | Observações |
|---|---|---|---|---|---|---|---|
| 1 | | `novo_pje` / `rearmado` | | | | | |
| 2 | | `novo_pje` / `rearmado` | | | | | |
| 3 | | `novo_pje` / `rearmado` | | | | | |
| 4 | | `novo_pje` / `rearmado` | | | | | |
| 5 | | `novo_pje` / `rearmado` | | | | | |
| 6 | | `novo_pje` / `rearmado` | | | | | |
| 7 | | `novo_pje` / `rearmado` | | | | | |
| 8 | | `novo_pje` / `rearmado` | | | | | |
| 9 | | `novo_pje` / `rearmado` | | | | | |
| 10 | | `novo_pje` / `rearmado` | | | | | |

## Consolidação técnica do ciclo

Preencher com os dados observados no dashboard, API ou SQLite.

| Campo | Valor observado |
|---|---|
| `ciclo_uuid` | |
| `status` final do ciclo | |
| `total_membros` | |
| `total_concluidos` | |
| `total_erros` | |
| `iniciado_em` | |
| `finalizado_em` | |
| Houve pausa por `aguardando_login` | `sim` / `não` |
| Houve pausa por `erro_pausado` | `sim` / `não` |

### Consulta sugerida para fechamento

```bash
docker exec custas-api sqlite3 /dados/custas.db "
SELECT uuid, status, total_membros, total_concluidos, total_erros, erro_msg
FROM agente_ciclos
WHERE uuid = '<ciclo_uuid>';
"

docker exec custas-api sqlite3 /dados/custas.db "
SELECT processo_id, numero_mascarado, origem, status_snapshot, status_atual, processado_em
FROM (
  SELECT
    m.processo_id,
    substr(m.numero, 1, 7) || '...' || substr(m.numero, -4) AS numero_mascarado,
    m.origem,
    m.status_snapshot,
    p.status AS status_atual,
    m.processado_em
  FROM agente_ciclo_membros m
  JOIN processos p ON p.id = m.processo_id
  WHERE m.ciclo_uuid = '<ciclo_uuid>'
)
ORDER BY processo_id;
"
```

## Evidência de emissão e anexação

Preencher somente se o lote tiver processos concluídos com emissão/anexo. O
schema atual registra isso em `evidencias_emissao`.

```bash
docker exec custas-api sqlite3 /dados/custas.db "
SELECT processo_id, etapa, referencia_arquivo, referencia_externa, atualizado_em
FROM evidencias_emissao
WHERE processo_id IN (
  SELECT processo_id FROM agente_ciclo_membros WHERE ciclo_uuid = '<ciclo_uuid>'
)
ORDER BY processo_id, etapa;
"
```

| Processo mascarado | Etapa | Referência registrada | Evidência anexada | Resultado |
|---|---|---|---|---|
| | `demonstrativo_emitido_sistj` | | | |
| | `demonstrativo_anexado_pje` | | | |

## Evidência de notificação operacional

Registrar apenas informação agregada. O texto de Telegram implementado hoje não
deve expor número de processo, parte, documento ou valor.

| Verificação | Evidência anexada | Resultado observado |
|---|---|---|
| Mensagem de resumo do lote enviada | | |
| Texto continha apenas totais e contagens por status | | |
| Não houve PII na notificação | | |

## Falhas e desvios observados

| Tipo | Descrição | Evidência | Tratamento |
|---|---|---|---|
| Bootstrap | | | |
| Sessão | | | |
| Emissão | | | |
| Anexação | | | |
| Infra | | | |

## Parecer final

| Item | Preencher |
|---|---|
| Resultado final | `aprovado` / `aprovado com ressalvas` / `reprovado` |
| Resumo executivo | |
| Limites que permanecem abertos | |
| Próximo responsável | |
| Ação seguinte | |
