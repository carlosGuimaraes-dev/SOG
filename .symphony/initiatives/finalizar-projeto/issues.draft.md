# Issues Draft: Finalizar projeto SOG para homologacao operacional

Source PRD: `.symphony/initiatives/finalizar-projeto/prd.md`

Status: draft for human review. Do not publish to Linear until approved.

Tracker: Linear via Symphony, project `sog-19e506c6c308`.

## Proposed Breakdown

1. Parent: Finalizar SOG para homologacao operacional controlada
   - Type: HITL parent
   - Blocked by: None
   - User stories covered: all initiative goals

2. Persistir ciclo do agente e formar lote fechado no Iniciar Agente
   - Type: AFK
   - Blocked by: parent only
   - User stories covered: cycle UUID, start label, membership snapshot, closed batch, current/last cycle visibility

3. Controlar execucao, pausa, retomada e relogin preservando o ciclo
   - Type: AFK
   - Blocked by: issue 2
   - User stories covered: cooperative stop, paused-cycle resume, session expiration, relogin banner state, no concurrent cycles

4. Reprocessar processos explicitamente com auditoria e consumo no proximo ciclo
   - Type: AFK
   - Blocked by: issue 2
   - User stories covered: Reprocessar for erro/pendente_manual/rejeitado, audit trail, next-cycle inclusion only

5. Proteger idempotencia de processos, guias, logs criticos e anexos PJE
   - Type: AFK
   - Blocked by: issues 2, 3, 4
   - User stories covered: repeat run safety, no duplicate internal artifacts, only rearmed processes rerun

6. Aprovar processo individualmente, emitir demonstrativo e anexar ao PJE
   - Type: AFK
   - Blocked by: issues 2, 5
   - User stories covered: per-process approval, emitido final status, failures isolated as erro

7. Notificar eventos operacionais por Telegram sem dados sensiveis
   - Type: AFK
   - Blocked by: issues 2, 3
   - User stories covered: relogin required, batch completed summary, fatal paused error, aggregate-only payloads

8. Recriar dashboard operacional com shadcn/UI, tabs e tema light/dark
   - Type: AFK
   - Blocked by: issues 2, 3, 4, 6, 7
   - User stories covered: Ciclo atual home, Processos, Historico, theme toggle, status badges, compact table, row actions

9. Validar Docker local e preparar evidencia da homologacao com 10 processos
   - Type: HITL
   - Blocked by: issues 2 through 8
   - User stories covered: local Docker readiness, assisted login, 10-process run, timing, bottlenecks, final outcomes

## Parent Issue

### Title

Finalizar SOG para homologacao operacional controlada

### Type

HITL parent

### What to build

Finalizar o SOG para uma homologacao operacional local Docker com SQLite, PJE/SISTJWEB reais, login manual pelo usuario, automacao headless depois da autenticacao, ciclos fechados com UUID, revisao humana por processo, aprovacao individual com emissao/anexo no PJE, dashboard operacional React + Vite + shadcn/UI e notificacoes Telegram agregadas.

### Acceptance criteria

- [ ] As subissues aprovadas cobrem ciclo fechado, pausa/retomada, reprocessamento, idempotencia, aprovacao/anexo, Telegram, dashboard e homologacao assistida.
- [ ] Nenhuma subissue exige PostgreSQL, VPS, SMTP obrigatorio, sidecar de backup ou reativacao da pasta `.kimi/`.
- [ ] O conjunto final permite demonstrar uma execucao local Docker com pelo menos 10 processos reais, incluindo evidencia de tempos, gargalos e resultados finais.

### Blocked by

None - can start immediately.

## Child Issue 1

### Title

Persistir ciclo do agente e formar lote fechado no Iniciar Agente

### Type

AFK

### What to build

Implementar o primeiro caminho completo de ciclo do agente: ao clicar em `Iniciar Agente`, o sistema cria um ciclo persistido com UUID, rotulo por data/hora, status inicial, snapshot fechado de membros e contadores agregados. O lote deve incluir processos novos capturados do PJE configurado no momento do start e processos conhecidos explicitamente rearmados. Processos descobertos depois ficam fora do ciclo ativo.

### Tasks / subtasks

- [ ] Adicionar persistencia SQLite para ciclos, membros do ciclo, tempos e contadores agregados.
- [ ] Espelhar o schema necessario entre agente/shared onde o projeto ja exige duplicidade de schema.
- [ ] Implementar formacao de lote fechado no `Iniciar Agente`.
- [ ] Garantir que processos ja acionaveis nao entrem de novo automaticamente no lote.
- [ ] Expor API minima para ciclo atual/ultimo ciclo, detalhe com UUID e membros do snapshot.
- [ ] Mostrar um resumo minimo do ciclo atual no dashboard sem ainda redesenhar toda a UI.
- [ ] Cobrir com testes de criacao de ciclo, UUID persistido, snapshot fechado e API de consulta.

### Acceptance criteria

- [ ] `Iniciar Agente` cria um ciclo com UUID persistido, rotulo de data/hora e snapshot de membros.
- [ ] A lista de membros do ciclo nao muda quando novos processos aparecem depois do start.
- [ ] O detalhe do ciclo retorna UUID e membros a partir do snapshot persistido, nao por inferencia de status atual.
- [ ] Testes automatizados provam criacao, persistencia, snapshot e consulta do ciclo.

### Blocked by

None - can start immediately.

## Child Issue 2

### Title

Controlar execucao, pausa, retomada e relogin preservando o ciclo

### Type

AFK

### What to build

Completar o controle operacional do ciclo para que `Iniciar Agente`, `Parar Agente`, pausa por expiracao de sessao e retomada trabalhem sempre sobre o mesmo ciclo quando houver ciclo pausado. O stop deve ser cooperativo, preservar UUID/snapshot e impedir ciclos concorrentes na UI, API e agente.

### Tasks / subtasks

- [ ] Ajustar a maquina de estados do agente para running, stopping, paused/interrupted, relogin required e fatal paused error.
- [ ] Fazer `Parar Agente` parar depois do passo seguro atual, marcando o ciclo como pausado/interrompido.
- [ ] Fazer `Iniciar Agente` retomar ciclo pausado por padrao, sem criar novo ciclo.
- [ ] Preservar UUID, snapshot e tempos de pausa/retomada.
- [ ] Expor estado de controle para o dashboard, incluindo bloqueio de ciclo concorrente.
- [ ] Expor relogin-required state para a UI.
- [ ] Cobrir pause/resume, relogin-required e concorrencia com testes.

### Acceptance criteria

- [ ] Enquanto um ciclo roda, `Iniciar Agente` fica indisponivel e a API rejeita novo ciclo concorrente.
- [ ] `Parar Agente` preserva UUID e snapshot, e deixa o ciclo retomavel.
- [ ] Um novo `Iniciar Agente` com ciclo pausado retoma o mesmo UUID.
- [ ] Expiracao de sessao pausa o ciclo e exige relogin sem duplicar trabalho ja concluido.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.

## Child Issue 3

### Title

Reprocessar processos explicitamente com auditoria e consumo no proximo ciclo

### Type

AFK

### What to build

Adicionar a acao explicita `Reprocessar` no detalhe do processo para estados `erro`, `pendente_manual` e `rejeitado`. A acao deve registrar auditoria, marcar o processo para entrar no proximo ciclo iniciado e consumir essa marcacao uma unica vez quando o ciclo for formado.

### Tasks / subtasks

- [ ] Modelar flag/estado de rearmamento consumivel pelo proximo ciclo.
- [ ] Registrar auditoria/log da acao, com usuario/horario/motivo quando disponivel.
- [ ] Implementar endpoint de reprocessamento explicito.
- [ ] Impedir processamento imediato fora de um novo clique em `Iniciar Agente`.
- [ ] Incluir processos rearmados no snapshot do proximo ciclo e limpar a marcacao consumida.
- [ ] Expor a acao no detalhe do processo para os status elegiveis.
- [ ] Cobrir auditoria, elegibilidade e consumo unico com testes.

### Acceptance criteria

- [ ] Apenas `erro`, `pendente_manual` e `rejeitado` exibem/aceitam `Reprocessar`.
- [ ] `Reprocessar` nao inicia automacao imediatamente.
- [ ] O proximo ciclo inclui processos rearmados e consome a marcacao.
- [ ] A auditoria permite explicar quem rearmou, quando e qual processo entrou novamente no lote.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.

## Child Issue 4

### Title

Proteger idempotencia de processos, guias, logs criticos e anexos PJE

### Type

AFK

### What to build

Implementar guardas e testes para que reexecucoes nao dupliquem registros internos, guias/demonstrativos, logs criticos nem anexos PJE. Somente processos explicitamente rearmados podem ser processados de novo, e cada etapa sensivel deve reconhecer trabalho ja concluido antes de repetir.

### Tasks / subtasks

- [ ] Identificar chaves naturais/unicas para processo, guia/demonstrativo, log critico e anexo.
- [ ] Adicionar constraints ou guardas transacionais no SQLite/shared DB.
- [ ] Blindar pipeline para pular etapas ja concluidas quando o processo nao foi rearmado.
- [ ] Blindar emissao/anexo contra repeticao indevida.
- [ ] Registrar evidencia de skip/idempotencia sem poluir logs criticos duplicados.
- [ ] Cobrir reexecucao de ciclo e reprocessamento rearmado com testes.

### Acceptance criteria

- [ ] Reexecutar com processos ja tratados nao cria duplicata de processo, guia/demonstrativo ou log critico.
- [ ] Anexo PJE nao e repetido sem confirmacao/estado que justifique a reemissao.
- [ ] Processo rearmado pode entrar no ciclo seguinte sem reusar indefinidamente o mesmo rearmamento.
- [ ] Testes automatizados provam o comportamento para rerun normal e rerun rearmado.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.
- Child Issue 2: Controlar execucao, pausa, retomada e relogin preservando o ciclo.
- Child Issue 3: Reprocessar processos explicitamente com auditoria e consumo no proximo ciclo.

## Child Issue 5

### Title

Aprovar processo individualmente, emitir demonstrativo e anexar ao PJE

### Type

AFK

### What to build

Finalizar o caminho de revisao humana por processo: processos em `aguardando_aprovacao` podem ser revisados individualmente; a aprovacao dispara emissao do demonstrativo e anexo no PJE real do respectivo processo; sucesso termina em `emitido`; falha termina em `erro` com mensagem clara e sem bloquear os demais membros do ciclo.

### Tasks / subtasks

- [ ] Garantir endpoint/acao de aprovacao por processo.
- [ ] Integrar aprovacao com emissao do demonstrativo e anexo no PJE.
- [ ] Registrar status final `emitido` somente apos emissao/anexo bem-sucedidos.
- [ ] Registrar `erro` com `erro_msg` clara quando emissao ou anexo falhar.
- [ ] Garantir que falha individual nao bloqueie outros processos do ciclo.
- [ ] Atualizar contadores do ciclo apos aprovacao, emissao e erro.
- [ ] Cobrir aprovacao feliz e falhas de emissao/anexo com testes usando mocks onde necessario.

### Acceptance criteria

- [ ] Cada processo e aprovado separadamente, sem aprovacao em lote.
- [ ] Aprovacao bem-sucedida emite demonstrativo, anexa ao PJE e marca `emitido`.
- [ ] Falhas de emissao/anexo ficam em `erro` com mensagem investigavel.
- [ ] O ciclo continua visivel e acionavel mesmo com falhas individuais.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.
- Child Issue 4: Proteger idempotencia de processos, guias, logs criticos e anexos PJE.

## Child Issue 6

### Title

Notificar eventos operacionais por Telegram sem dados sensiveis

### Type

AFK

### What to build

Implementar notificacoes Telegram notify-only para os tres eventos da homologacao: sessao expirada/relogin necessario, resumo de lote concluido e erro fatal com agente pausado. As mensagens devem usar apenas dados agregados e nunca incluir numero de processo, partes ou detalhes de documento.

### Tasks / subtasks

- [ ] Adicionar `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` em configuracao e `.env.example`.
- [ ] Validar Telegram como requisito da homologacao local, sem tornar SMTP bloqueante.
- [ ] Implementar sender Telegram com HTTP mockavel.
- [ ] Disparar notificacao em relogin required.
- [ ] Disparar resumo agregado ao completar ciclo.
- [ ] Disparar erro fatal com agente pausado.
- [ ] Cobrir privacidade do payload e falhas de envio com testes.

### Acceptance criteria

- [ ] Telegram envia apenas notificacoes, sem aceitar comandos.
- [ ] Resumo de lote contem total, contagens por status, tempo total e dica para acessar dashboard.
- [ ] Mensagens nao incluem numero de processo, nome de parte ou detalhe documental.
- [ ] Testes com HTTP mockado provam eventos, formato e privacidade.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.
- Child Issue 2: Controlar execucao, pausa, retomada e relogin preservando o ciclo.

## Child Issue 7

### Title

Recriar dashboard operacional com shadcn/UI, tabs e tema light/dark

### Type

AFK

### What to build

Recriar o dashboard operacional mantendo React + Vite e trocando os componentes atuais de UI por shadcn/UI. A tela inicial apos login deve ser `Ciclo atual`, com tabs `Ciclo atual`, `Processos` e `Historico`, controle stateful `Iniciar Agente`/`Parar Agente`, banner de relogin, tabela compacta de processos do ciclo, acoes por status, filtros rapidos e tema light/dark com icone Sun/Moon e tooltip.

### Tasks / subtasks

- [ ] Instalar/configurar shadcn/UI compativel com Vite.
- [ ] Substituir os componentes primitivos atuais por componentes shadcn/UI equivalentes.
- [ ] Implementar shell autenticado com tabs `Ciclo atual`, `Processos` e `Historico`.
- [ ] Tornar `Ciclo atual` a home apos login.
- [ ] Adicionar toggle light/dark icon-only com tooltip, `prefers-color-scheme` inicial e persistencia em `localStorage`.
- [ ] Implementar badges compactos por status: azul, vermelho, amber, verde e cinza/vermelho discreto.
- [ ] Implementar tabela do ciclo com colunas `Processo`, `Status`, `Etapa atual`, `Guia`, `Tempo`, `Acao`.
- [ ] Implementar row actions contextuais por status.
- [ ] Implementar `Processos` com filtros rapidos e foco inicial em itens acionaveis.
- [ ] Implementar `Historico` com historico de processos e de ciclos separado por filtro simples.
- [ ] Validar legibilidade em light/dark e volume medio de 50 processos.

### Acceptance criteria

- [ ] Apos login, a primeira tela e `Ciclo atual`.
- [ ] Tabs `Ciclo atual`, `Processos` e `Historico` renderizam e navegam corretamente.
- [ ] Tema light/dark respeita preferencia inicial, persiste escolha e usa apenas icone Sun/Moon com tooltip.
- [ ] Row actions batem com os estados definidos no PRD.
- [ ] A UI usa shadcn/UI em vez dos primitivos anteriores e continua React + Vite.
- [ ] Evidencia Playwright cobre tabs, tabela, badges, tema e banner de relogin.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.
- Child Issue 2: Controlar execucao, pausa, retomada e relogin preservando o ciclo.
- Child Issue 3: Reprocessar processos explicitamente com auditoria e consumo no proximo ciclo.
- Child Issue 5: Aprovar processo individualmente, emitir demonstrativo e anexar ao PJE.
- Child Issue 6: Notificar eventos operacionais por Telegram sem dados sensiveis.

## Child Issue 8

### Title

Validar Docker local e preparar evidencia da homologacao com 10 processos

### Type

HITL

### What to build

Preparar e executar a validacao final de homologacao operacional em Docker local. A validacao deve subir API, frontend, agente, nginx e SQLite; guiar o usuario pelo login manual PJE/SISTJWEB; rodar um ciclo com pelo menos 10 processos reais; registrar tempos, gargalos, resultados finais, idempotencia de rerun e riscos residuais.

### Tasks / subtasks

- [ ] Atualizar checklist de ambiente local Docker e variaveis obrigatorias.
- [ ] Validar que SMTP nao bloqueia startup e que Telegram esta configurado.
- [ ] Executar smoke de API, frontend, agente, nginx e volume SQLite.
- [ ] Registrar evidencia de login manual e continuacao headless apos autenticacao.
- [ ] Rodar ciclo assistido com pelo menos 10 processos reais.
- [ ] Registrar total do ciclo, tempo por processo, gargalos e resultados finais.
- [ ] Validar pelo menos um caminho de aprovacao com emissao/anexo quando operacionalmente permitido.
- [ ] Reexecutar cenario suficiente para provar idempotencia sem duplicidades.
- [ ] Registrar riscos residuais e pendencias externas.

### Acceptance criteria

- [ ] `docker-compose up --build -d` sobe os servicos necessarios para a homologacao local.
- [ ] O usuario consegue autenticar manualmente e o agente segue headless depois do login.
- [ ] Um ciclo com pelo menos 10 processos reais termina com todos os membros em estado acionavel ou final.
- [ ] A evidencia registra tempos, gargalos, resultados e qualquer falha individual.
- [ ] O rerun nao duplica registros, guias, logs criticos ou anexos PJE.

### Blocked by

- Child Issue 1: Persistir ciclo do agente e formar lote fechado no Iniciar Agente.
- Child Issue 2: Controlar execucao, pausa, retomada e relogin preservando o ciclo.
- Child Issue 3: Reprocessar processos explicitamente com auditoria e consumo no proximo ciclo.
- Child Issue 4: Proteger idempotencia de processos, guias, logs criticos e anexos PJE.
- Child Issue 5: Aprovar processo individualmente, emitir demonstrativo e anexar ao PJE.
- Child Issue 6: Notificar eventos operacionais por Telegram sem dados sensiveis.
- Child Issue 7: Recriar dashboard operacional com shadcn/UI, tabs e tema light/dark.
