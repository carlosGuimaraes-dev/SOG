# Finalizar projeto SOG para homologacao operacional

## Elicitation Status

Status: complete.

The human owner confirmed the intended homologation scope. This initiative is ready for `diagnose`.

## Problem

O SOG tem implementacoes e documentacao acumuladas para o pipeline de custas processuais do TJDFT, mas ainda precisa de uma etapa final de organizacao para homologacao operacional. O estado atual mistura entregas ja registradas como concluidas, ressalvas de code review, roadmap tecnico, configuracoes de ambiente e historico legado da pasta `.kimi`.

Sem uma initiative Symphony, o risco e transformar "finalizar o projeto" em trabalho ad hoc: corrigir itens sem prioridade clara, reabrir fluxos historicos que nao sao mais operacionais, ou exportar tickets sem criterio verificavel de pronto para homologacao.

## Goal

Definir o escopo de finalizacao do SOG em uma initiative rastreavel pelo Symphony Initiative Layer, com diagnostico, PRD, issues revisadas e aprovacao humana antes de qualquer exportacao para Linear.

O resultado esperado e um conjunto pequeno e verificavel de issues que leve o projeto a um estado de homologacao operacional: documentado, configuravel, testavel, seguro o suficiente para ambiente controlado e com pendencias explicitas quando dependerem de credenciais ou acesso externo.

## Actors

- Operadora/contadora do TJDFT: usa o dashboard para revisar processos, aprovar custas e acompanhar emissao.
- Administrador tecnico do SOG: configura ambiente, credenciais, deploy e operacao local/servidor.
- Agente automatizado: monitora PJE, consulta Datajud, preenche SISTJWEB e produz evidencias.
- API/dashboard: expostos aos operadores para fila, detalhe, historico, autenticacao e aprovacao.
- Linear/GitHub via Symphony: fonte de rastreabilidade para issues, PRs, validacao e conclusao.

## Current Understanding

- O repositorio usa Symphony em modo `initiative-plus-execution`.
- O tracker configurado e Linear, projeto `sog-19e506c6c308`.
- A ordem de fases e `elicit`, `diagnose`, `prd`, `issues`, `review`, `approve`, `handoff`, `export`.
- A fase `approve` e interativa e a exportacao exige aprovacao previa.
- A pasta `.kimi/` e apenas historico; nao deve ser usada como orquestrador ativo.
- `docs/agents/*.md` confirma que os artefatos de planejamento ficam em `.symphony/initiatives/<slug>/` e que o fluxo usa estados Symphony em vez de labels ad hoc.
- O alvo desta initiative e homologacao operacional controlada, nao producao real.
- O ambiente obrigatorio da homologacao e apenas local Docker.
- A diretriz de produto/engenharia e manter o sistema o mais simples possivel; esta homologacao nao deve virar um projeto enterprise grade.
- SQLite e o unico banco no escopo desta homologacao local Docker; migracao para PostgreSQL e backup sidecar ficam fora do escopo.
- A configuracao minima para homologacao local Docker e `DASHBOARD_SENHA_HASH`, `JWT_SECRET_KEY`, `DATAJUD_API_KEY`, `PJE_URL`, `PJE_ETIQUETA`, `SISTJ_URL`, `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.
- SMTP/notificacao por e-mail fica para depois e nao bloqueia esta homologacao.
- Se a sessao do PJE ou SISTJWEB expirar durante o lote, o ciclo deve pausar, notificar o usuario para logar novamente e depois continuar o mesmo lote sem duplicar o que ja foi concluido.
- Notificacao apenas por e-mail nao e suficiente para sessao expirada; a homologacao deve incluir notificacao no dashboard e Telegram. Telegram e apenas notificacao, sem comandos remotos. O codigo atual so tem notificador por e-mail, entao Telegram e requisito novo.
- Telegram deve ser configurado por variaveis de ambiente no agente: `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`, sem persistir segredo no banco ou no codigo.
- Telegram deve notificar apenas tres eventos nesta homologacao: sessao expirada/relogin necessario, lote concluido com resumo e erro fatal que pausa o agente.
- O resumo de lote no Telegram deve conter apenas dados agregados: total, contagens por status, tempo total e indicacao para abrir o dashboard. Nao deve incluir numeros de processo, nomes de partes ou detalhes documentais.
- A validacao da homologacao deve combinar testes automatizados alvo para regras internas com execucao real assistida em local Docker usando lote de 10 processos. Nao e requisito automatizar E2E completo contra PJE/SISTJWEB reais.
- A homologacao deve exercitar PJE e SISTJWEB reais, com credenciais reais inseridas interativamente pelo usuario quando necessario.
- Apos o usuario clicar em "Iniciar Agente", ele deve inserir login, senha e 2FA manualmente; depois da autenticacao, o agente deve seguir em modo headless ate a etapa em que o usuario precisa conferir o que foi feito.
- A fronteira entre automacao e revisao humana ocorre apenas quando todos os processos do ciclo do agente tiverem sido processados e todas as guias estiverem prontas para analise/aprovacao do usuario no status `aguardando_aprovacao`.
- O ciclo do agente e um lote fechado formado no clique em "Iniciar Agente": processos novos encontrados na pasta/etiqueta PJE configurada, mais processos ja conhecidos que tenham sido explicitamente selecionados/rearmados pelo usuario. Processos que aparecerem depois pertencem a outro ciclo.
- Cada ciclo deve ter UUID persistido e rotulo por data/hora de inicio. Na UI, a data/hora deve ser o rotulo principal; o UUID deve aparecer copiavel no detalhe do ciclo e nao precisa aparecer na tabela principal.
- A homologacao deve usar um lote minimo de 10 processos para analisar idempotencia e estresse basico do bot.
- Se o usuario clicar em "Iniciar Agente" novamente com processos ja processados, o agente nao deve duplicar registros, guias, logs criticos ou anexos no PJE. Processos em estado acionavel/final devem ser ignorados, salvo rearme explicito via "Reprocessar".
- O stress basico nao tem SLA rigido nesta homologacao, mas deve registrar tempo total do ciclo, tempo por processo e gargalos observados.
- A composicao do lote precisa ser persistida como snapshot no inicio do ciclo, sem depender de inferencia posterior por status atual dos processos.
- O rearme para reprocessamento deve acontecer pelo dashboard, no detalhe do processo, por uma acao explicita como "Reprocessar", disponivel para `erro`, `pendente_manual` e `rejeitado`. Essa acao deve registrar log/auditoria e marcar o processo para entrar no proximo lote iniciado pelo usuario.
- O dashboard precisa exibir uma visao de lote/ciclo do agente, incluindo membros do ciclo, progresso agregado, resultados acionaveis e excecoes, alem de historico basico de ciclos anteriores.
- O dashboard autenticado pode exibir numeros de processo e detalhes necessarios para revisao; a restricao de resumo agregado se aplica ao Telegram.
- O dashboard deve ter tema light/dark com toggle apenas por icone Sun/Moon e tooltip no cabecalho global. No primeiro acesso, deve seguir `prefers-color-scheme`; depois, a escolha manual fica persistida localmente.
- A direcao visual deve ser institucional discreta, neutra e operacional, com contraste claro para status.
- O dashboard deve manter React + Vite e usar shadcn/UI compatível com Vite. Nao migrar para Next.js.
- Todos os componentes atuais de UI devem ser substituidos por shadcn/UI no Vite, mantendo simplicidade e o escopo funcional da homologacao.
- A substituicao por shadcn/UI deve preservar paginas, rotas e fluxos atuais quando ainda fizerem sentido, evitando reestruturacao desnecessaria.
- Cores de status devem ser obvias, com badges pequenos e legiveis: `aguardando_aprovacao` azul, `erro` vermelho, `pendente_manual` amarelo/ambar, `emitido` verde, `rejeitado` cinza ou vermelho discreto.
- A primeira tela apos login deve ser um painel operacional do ciclo do agente, nao apenas uma fila simples. Esse painel deve priorizar status do agente, acao "Iniciar Agente", ciclo atual/ultimo ciclo, progresso do lote, contagens por status, alertas de relogin e lista de processos do ciclo para revisao individual.
- A navegacao do dashboard deve usar tabs separadas, com `Ciclo atual` como primeira tab, seguida de `Processos` e `Historico`.
- A tab `Processos` deve listar todos os processos do banco, com filtros rapidos e foco padrao nos itens que precisam de acao humana.
- A tab `Historico` deve incluir historico de processos e historico de ciclos do agente, separados por filtro/segmento simples.
- A UI deve seguir "menos e mais": na tab `Ciclo atual`, usar resumo compacto e tabela compacta de processos, sem graficos obrigatorios. Embora a homologacao use 10 processos, a operacao diaria esperada e cerca de 50 processos em media.
- A tabela compacta do ciclo deve ter as colunas minimas `Processo`, `Status`, `Etapa atual`, `Guia`, `Tempo` e `Acao`; detalhes completos ficam no detalhe do processo.
- A acao por linha deve ser contextual: `Revisar` para `aguardando_aprovacao`; `Ver erro`/`Reprocessar` para `erro` e `pendente_manual`; `Reprocessar` para `rejeitado`; `Ver comprovante/detalhe` para `emitido`; processos em execucao mostram apenas status, sem acao primaria.
- Quando houver relogin necessario, a tab `Ciclo atual` deve exibir banner fixo no topo, alem da notificacao Telegram, com acao para abrir login/continuar autenticacao se tecnicamente possivel.
- O botao `Iniciar Agente` deve ficar desabilitado enquanto houver ciclo em execucao, para evitar ciclos concorrentes contra PJE/SISTJWEB, storage state e SQLite.
- Se houver ciclo pausado, `Iniciar Agente` deve retomar esse ciclo por padrao, sem oferecer criacao de novo ciclo nesse caminho.
- A homologacao deve incluir controle simples do agente: o mesmo botao muda de estado conforme o ciclo. Quando estiver rodando, mostra `Parar Agente`; quando estiver pausado/interrompido, o proprio controle indica a retomada/status apropriado. A parada e cooperativa apos a etapa atual, com snapshot do lote preservado e sem cancelamento complexo por processo.
- Pausa/interrupcao e retomada devem preservar o mesmo UUID do ciclo, porque continuam o mesmo lote/snapshot.
- Encerramento/descarte manual definitivo de ciclo pausado fica fora desta homologacao inicial.
- Erros tecnicos, dados ausentes ou regras nao mapeadas nao bloqueiam o lote inteiro. O processo afetado deve ir para `pendente_manual` ou `erro`, com `erro_msg` e logs claros, enquanto os demais continuam ate `aguardando_aprovacao`.
- A revisao/aprovacao humana acontece processo por processo. Aprovacao em lote fica fora do escopo desta homologacao.
- Quando o usuario aprova um processo, essa aprovacao autoriza a emissao do demonstrativo e o anexo do demonstrativo ao respectivo processo no PJE real.
- Apos emissao e anexo bem-sucedidos, o status final de sucesso no SOG deve ser `emitido`. Falha na emissao ou anexo deve resultar em `erro`, com logs e `erro_msg`.
- O codigo atual ja aponta para esse desenho em `agente/src/modulos/auth_manager.py`: login manual em browser visivel, storage state salvo e reabertura posterior em headless.

## In Scope

- Diagnosticar o estado real do backend, agente, frontend, infra, documentacao e testes.
- Identificar pendencias bloqueantes para homologacao operacional.
- Separar pendencias de produto, seguranca, operacao, dados/credenciais e deploy.
- Transformar pendencias em issues pequenas, verificaveis e independentes quando possivel.
- Definir criterios de validacao por area, incluindo testes automatizados, checks Docker e prova Playwright quando houver UI.
- Definir testes alvo e roteiro de execucao real assistida com 10 processos.
- Avaliar introducao/uso de shadcn/UI mantendo o frontend atual React + Vite.
- Substituir todos os componentes UI atuais por shadcn/UI, sem migrar framework.
- Preservar rotas e fluxos existentes quando forem compativeis com o novo painel/tabs.
- Definir um fluxo de homologacao assistida para PJE/SISTJWEB reais sem persistir credenciais no repositorio.
- Definir notificacao de sessao expirada por dashboard e Telegram para solicitar novo login do usuario.
- Validar que o clique em "Iniciar Agente" suporta autenticacao manual e que a automacao posterior roda headless ate a revisao humana.
- Validar que todos os processos do ciclo do agente chegam ao ponto de revisao com suas guias prontas antes de considerar a automacao concluida.
- Garantir que a execucao trabalhe sobre lote fechado capturado no inicio do ciclo.
- Validar idempotencia e estresse basico do bot com lote minimo de 10 processos.
- Validar que nova execucao sobre processos ja tratados nao duplica registros, guias, logs criticos ou anexos no PJE.
- Registrar tempos e gargalos do ciclo de 10 processos, sem reprovar por SLA rigido.
- Validar o fluxo real por execucao assistida, nao por E2E externo totalmente automatizado.
- Garantir persistencia do snapshot de membros do lote no inicio do ciclo.
- Garantir que reprocessamento so aconteca para processos explicitamente selecionados/rearmados pelo usuario.
- Garantir acao de rearme/reprocessamento no detalhe do processo, com log/auditoria.
- Garantir visao de lote/ciclo no dashboard para mostrar progresso, conclusao do ciclo e historico basico de ciclos anteriores.
- Fazer do painel de ciclo do agente a tela principal pos-login do dashboard.
- Organizar a navegacao principal por tabs separadas: ciclo atual, processos e historico.
- Manter UI compacta e operavel para media diaria de 50 processos.
- Garantir que falhas individuais gerem estados acionaveis (`pendente_manual` ou `erro`) sem interromper o restante do lote.
- Garantir revisao e aprovacao individual por processo.
- Validar que a aprovacao individual dispara emissao do demonstrativo e anexo no PJE real do respectivo processo.
- Validar `emitido` como status final de sucesso apos anexo no PJE.
- Manter rastreabilidade por Linear/GitHub conforme `SYMPHONY.md`.

## Out of Scope

- Reativar papeis, waves ou validadores da `.kimi` como processo operacional.
- Exportar issues para Linear antes das fases `diagnose`, `prd`, `issues`, `review` e `approve`.
- Marcar qualquer issue como `Done` sem PR mergeado, salvo se a propria issue permitir conclusao direta.
- Migracao para PostgreSQL nesta homologacao.
- Backup sidecar nesta homologacao.
- Configuracao SMTP/notificacao por e-mail nesta homologacao.
- Comandos via Telegram.
- Encerramento/descarte manual definitivo de ciclos pausados.
- Arquitetura enterprise grade ou controles pesados que nao sejam necessarios para validar a homologacao local controlada.
- Inserir credenciais reais em arquivos versionados ou na conversa.
- Acessar PJE/SISTJWEB real sem credenciais e permissao explicita do usuario.
- VPS, deploy de producao e homologacao remota.
- Aprovacao em lote.

## Constraints

- Mudancas de planejamento devem ficar dentro de `.symphony/initiatives/finalizar-projeto/`.
- Execucao de tickets deve acontecer em workspaces Symphony, nao diretamente no planejamento, quando a initiative for exportada.
- A homologacao obrigatoria deve rodar em local Docker.
- Solucoes devem privilegiar simplicidade operacional e mudancas pequenas.
- `.env` e segredos nao devem ser commitados.
- PJE e SISTJWEB reais exigem credenciais reais inseridas interativamente pelo usuario.
- Depois da autenticacao manual, a automacao deve operar headless ate a conferencia humana.
- A conferencia humana comeca somente no status `aguardando_aprovacao`, quando todas as guias do ciclo estiverem prontas.
- Novos processos que surgirem na pasta/etiqueta PJE depois do inicio do ciclo nao devem alterar o criterio de conclusao do ciclo atual.
- Processos ja existentes em `erro`, `pendente_manual`, `rejeitado` ou outros estados nao devem ser reprocessados automaticamente sem selecao/rearme explicito do usuario.
- Historico de ciclos deve se basear no snapshot persistido de membros do lote, nao em inferencia por status atual.
- O rearme precisa deixar rastro auditavel e ser consumido apenas pelo proximo lote iniciado pelo usuario.
- A conclusao do lote exige que todos os processos tenham um resultado acionavel: guia pronta em `aguardando_aprovacao`, ou excecao visivel em `pendente_manual`/`erro`.
- Acesso externo a PJE, SISTJWEB, Datajud, SMTP, GitHub e Linear pode bloquear validacoes completas.
- Trabalho de UI deve incluir prova Playwright quando aplicavel.
- O criterio de conclusao do Symphony exige PR e merge para execucao regular.

## Open Questions

## Success Criteria

- A fase `diagnose` consegue produzir um mapa atual de pendencias com evidencia de arquivos, testes e comandos.
- O PRD define claramente o que significa "pronto para homologacao operacional".
- As issues aprovadas cobrem todos os bloqueadores encontrados, sem duplicar itens historicos ja resolvidos.
- Cada issue tem validacao objetiva, incluindo comando/teste esperado e evidencia a registrar no Workpad.
- Nenhuma fase `approve`, `handoff` ou `export` e executada antes da revisao e aprovacao humana da initiative.
