# Pipeline de Custas Processuais TJDFT

Contexto do SOG, um sistema de apoio ao operador que acompanha processos,
prepara custas e pausa em pontos que exigem decisao humana.

## Language

**Operador**:
A pessoa que usa o SOG para acompanhar processos, revisar custas e autorizar
acoes que dependem de julgamento humano.
_Avoid_: usuario do dashboard, admin

**Ferramenta local assistida**:
O modo de existencia do SOG no escopo atual: uma ferramenta local operada com
intervencao humana, sem contas de dashboard nem concorrencia entre usuarios.
_Avoid_: sistema multiusuario, portal auditavel por pessoa

**Executavel pronto**:
A forma esperada de entrega do SOG para o operador Windows: instalar e usar sem
entender ou instalar manualmente Node.js, npm, Docker, Docker Compose ou Docker
Desktop.
_Avoid_: instalacao guiada de dependencias tecnicas, roteiro de terminal

**Instalacao local completa**:
Resultado esperado do executavel pronto: runtime preparado, SOG baixado,
configurado e iniciado na maquina local, com o operador apenas confirmando
permissoes e abrindo o dashboard.
_Avoid_: pos-instalacao manual, comandos de compose, configuracao por terminal

**Casca local**:
O papel do Electron no SOG: preparar runtime, iniciar a instalacao local e abrir
o dashboard. Ele nao deve ter painel proprio nem virar uma experiencia
operacional separada do dashboard.
_Avoid_: segundo painel operacional, app paralelo ao dashboard, painel Electron

**Configuracao operacional**:
Configuracao do SOG feita como aba dentro do dashboard principal, depois que a
casca local preparou a maquina. Ela pertence ao fluxo operacional do SOG.
_Avoid_: wizard tecnico permanente, configuracao fora do dashboard, configuracao no Electron

**Aba de configuracao**:
A area do dashboard principal onde o operador ajusta configuracoes do SOG. Ela
substitui qualquer painel de configuracao proprio do Electron; o que hoje estiver
no Electron como configuracao deve migrar para essa aba.
_Avoid_: painel Electron, configurador separado, app de configuracao

**Atalho tecnico de distribuicao**:
Um caminho auxiliar para baixar ou publicar o instalador do SOG, usado por quem
opera a distribuicao. Ele nao e a jornada principal do operador leigo.
_Avoid_: fluxo do usuario final, instalacao por terminal

**Runtime interno**:
Dependencias tecnicas necessarias para o SOG funcionar, resolvidas pelo
instalador ou pelo aplicativo sem virar tarefa do operador.
_Avoid_: pre-requisito manual, ferramenta do usuario

**Preparo automatizado do runtime**:
A verificacao e instalacao guiada, dentro do executavel do SOG, das dependencias
tecnicas necessarias na maquina local do operador. O executavel verifica Node.js,
npm e Docker CLI; quando algo falta, pede autorizacao na interface e continua a
instalacao local.
_Avoid_: checklist manual, pedir para o operador instalar dependencias fora do SOG

**Docker CLI automatizado**:
A via operacional preferida para o SOG preparar e subir seus containers na
maquina local. Mesmo quando Docker Desktop existir, o operador nao deve depender
da interface grafica ou de conhecimento sobre Docker Desktop.
_Avoid_: Docker Desktop como jornada, abrir Docker Desktop, esperar GUI

**Docker Desktop**:
Produto grafico do Docker que exige interacao e conhecimento minimo do operador.
No SOG, ele nao e a via operacional do usuario final.
_Avoid_: instalar pelo operador, usar como passo do fluxo

**Autorizacao de instalacao local**:
Consentimento explicito do operador, pela interface do executavel, para o SOG
preparar dependencias tecnicas ausentes na maquina local.
_Avoid_: instalacao silenciosa sem consentimento, instrucao de terminal

**Elevacao explicada**:
Pedido de permissao elevada do Windows feito pelo executavel quando o preparo
automatizado do runtime exigir instalacao ou configuracao local. A interface deve
explicar o que sera instalado antes de acionar a elevacao.
_Avoid_: UAC surpresa, permissao sem contexto

**WSL interno**:
Dependencia tecnica do Windows usada quando necessaria para o runtime de
containers. Se estiver ausente ou desabilitada, o executavel deve preparar por
baixo, pedindo permissao ao operador, sem transformar WSL em tarefa manual.
_Avoid_: pedir para o operador instalar WSL, tutorial de Windows

**Retomada apos reinicializacao**:
Continuidade do preparo automatizado quando o Windows exigir reinicializacao
para concluir runtime interno, WSL ou virtualizacao. A reinicializacao e uma
interrupcao prevista, nao uma falha generica.
_Avoid_: perder estado da instalacao, mandar o operador recomecar

**Diagnostico para suporte**:
Registro tecnico exibido ou exportado quando o SOG nao consegue resolver uma
etapa automaticamente. O operador deve ver orientacao simples e dados de contato
como telefone e email; detalhes tecnicos ficam para suporte.
_Avoid_: erro cru para operador, stack trace como instrucao

**Modo exposto**:
Uma hipotese futura em que o dashboard seria publicado fora do ambiente local.
Ele esta fora do escopo atual do SOG.
_Avoid_: tratar como requisito atual, manter login local por precaucao

**Rastreabilidade operacional**:
O registro do que aconteceu no fluxo do SOG, suficiente para entender estados,
decisoes, erros e retomadas. Ela nao exige identificar uma pessoa por login do
dashboard.
_Avoid_: auditoria multiusuario, trilha por conta

**Dashboard local**:
O painel de trabalho do operador no SOG. Ele nao representa uma identidade
propria nem exige login proprio.
_Avoid_: portal autenticado, area administrativa

**Login do dashboard**:
Autenticacao propria para entrar no Dashboard local. No modo local do SOG, esse
conceito nao existe.
_Avoid_: confundir com login manual externo

**Login manual externo**:
A autenticacao feita pelo operador diretamente em sistemas externos como PJe e
SISTJWEB. O SOG pode depender dessa sessao, mas nao guarda a senha desses
sistemas.
_Avoid_: senha do SOG, login do dashboard

**Navegador de sessao do SOG**:
Instancia visivel de navegador aberta pelo SOG para PJe e SISTJWEB, com perfil
persistente, onde o operador faz login manual e 2FA no proprio sistema externo.
O agente deve trabalhar nessa sessao original, sem copiar storage state para
outro navegador.
_Avoid_: varias instancias de Chromium, captura de sessao copiada, navegador efemero

**Abertura assistida de sistema externo**:
Acao no dashboard que abre PJe ou SISTJWEB no Navegador de sessao do SOG para o
operador concluir o login manual externo. O SOG deve dar tempo ao operador para
2FA e so validar/operar depois da sessao estar ativa.
_Avoid_: abrir e fechar automaticamente, timeout antes do 2FA

**Abertura independente por sistema**:
Cada sistema externo, PJe e SISTJWEB, tem sua propria acao de abertura e
validacao no dashboard. Um login nao deve bloquear nem substituir o outro.
_Avoid_: botao unico para todos os logins, fluxo acoplado

**Aprovacao humana**:
A decisao explicita do operador antes de uma acao sensivel continuar, como
emitir ou anexar documentos.
_Avoid_: processamento automatico total, aprovacao implicita

**Acao do operador local**:
Uma acao humana feita no Dashboard local sem identificar uma pessoa especifica.
Ela registra que houve intervencao do operador, nao que houve usuario autenticado
no dashboard.
_Avoid_: usuario autenticado, conta do operador, admin

**Origem da tarefa**:
A fonte que iniciou uma tarefa operacional, como uma acao do operador local ou
um fluxo interno do SOG. Ela nao identifica necessariamente uma pessoa.
_Avoid_: criado por, autor, usuario

**Contrato compartilhado**:
A linguagem comum de dados usada por agente, API e dashboard para representar
processos, tarefas, ciclos e estados. No SOG, essa fonte canonica pertence ao
contexto compartilhado.
_Avoid_: schema paralelo, modelo duplicado, copia local

**Banco compartilhado**:
O armazenamento local usado pelo SOG para coordenar agente, API e dashboard. O
seu schema pertence ao contrato compartilhado, nao ao agente isoladamente.
_Avoid_: banco do agente, schema do agente

**Contrato de apresentacao da API**:
Uma forma de resposta criada pela API para entregar uma visao especifica ao
dashboard. Ele pode existir quando agrega ou formata o contrato compartilhado,
mas nao deve redefinir a linguagem comum.
_Avoid_: duplicar modelo compartilhado, schema concorrente

**Modelo de tela**:
Uma adaptacao feita pelo frontend para exibir melhor dados recebidos da API,
como labels, agrupamentos, tons visuais e ordem de apresentacao. Ele nao e fonte
de verdade de dominio nem redefine contrato da API.
_Avoid_: contrato paralelo, enum concorrente, regra de dominio no frontend

**Duplicacao de dominio**:
Uma copia concorrente de conceitos, modelos ou schema que deveriam pertencer ao
contrato compartilhado. No SOG, duplicacao de dominio e erro; duplicacao so e
aceitavel quando for apresentacao especifica.
_Avoid_: manter duas fontes de verdade

**Fronteira de dominio**:
Uma separacao conceitual entre responsabilidades do SOG, como processos e
aprovacao, agente e ciclos, tarefas e sessoes externas, e infraestrutura de
banco. A fronteira existe para evitar mistura de linguagem, nao para diminuir
arquivo por estetica.
_Avoid_: separar por tamanho, modulo artificial

**Processos e aprovacao**:
Fronteira de dominio que acompanha processos, dados extraidos, evidencias,
decisoes humanas e retomadas ligadas a aprovacao.
_Avoid_: fila generica, tela de processo

**Agente e ciclos**:
Fronteira de dominio que descreve a execucao local do agente, seus comandos,
ciclos, membros e estados de andamento.
_Avoid_: job global, worker remoto

**Tarefas e sessoes externas**:
Fronteira de dominio que representa tarefas operacionais enviadas a PJe ou
SISTJWEB e o estado das sessoes externas necessarias para executa-las.
_Avoid_: fila multiusuario, login do dashboard

**Tarefa operacional**:
Uma unidade de trabalho do SOG para executar uma acao externa ou retomavel, como
consultar PJe, preencher SISTJWEB ou reautenticar uma sessao externa. Ela faz
parte do dominio atual.
_Avoid_: tarefa generica, job de usuario

**Estado operacional**:
A informacao que o operador precisa ver para entender progresso, bloqueios e
retomadas do SOG. Ele pode ser derivado de tarefas operacionais, mas nao exige
que o operador administre uma fila tecnica.
_Avoid_: painel de fila tecnica, administracao de jobs

**Automacao por sistema externo**:
Separacao da automacao conforme o sistema externo alvo, como PJe e SISTJWEB.
Essa complexidade e justificada quando fluxos, seletores, downloads e timeouts
sao diferentes.
_Avoid_: unificacao artificial, camada generica sem necessidade

**Concorrencia local controlada**:
Coordenacao do Banco compartilhado para evitar corrida entre API, agente e
dashboard em aprovacao, ciclo e retomada. Transacoes fazem parte dessa
complexidade justificada.
_Avoid_: escrita concorrente casual, estado sem transacao

**Dashboard por secoes**:
Organizacao do dashboard principal em secoes ou componentes menores para
representar areas operacionais diferentes. Essa divisao e aceitavel quando nao
duplica contrato de dominio.
_Avoid_: pagina monolitica, componente que redefine contrato

**Infraestrutura de banco**:
Fronteira tecnica minima para conexao, inicializacao e manutencao do Banco
compartilhado. Ela nao deve carregar linguagem de processo, agente ou tarefa.
_Avoid_: modulo de regras, servico geral

**Contexto compartilhado**:
O lugar conceitual onde vivem contratos e operacoes comuns a agente, API e
dashboard. Ele pode ser organizado por fronteiras de dominio sem devolver essas
responsabilidades para um runtime especifico.
_Avoid_: dominio da API, dominio do agente

## Example Dialogue

Dev: O dashboard local precisa pedir senha?

Domain expert: Nao. O operador ja esta no ambiente local do SOG; senha so entra
nos sistemas externos.

Dev: Entao o login manual externo e o login do dashboard sao a mesma coisa?

Domain expert: Nao. Login manual externo e PJe ou SISTJWEB. O dashboard local
nao tem login proprio.

Dev: Depois que o operador faz login em PJe e SISTJWEB, o agente deve copiar a
sessao para outro navegador?

Domain expert: Nao. O operador faz login no navegador de sessao do SOG, e o
agente trabalha nessa mesma sessao original.

Dev: O SOG pode abrir varias instancias de Chromium e fechar se demorar?

Domain expert: Nao. O operador precisa tempo para 2FA. O dashboard deve oferecer
abertura assistida de PJe e SISTJWEB e validar apenas depois do login concluido.

Dev: A abertura de PJe e SISTJWEB deve ser um unico botao?

Domain expert: Nao. Os botoes devem ser separados e independentes, porque cada
sistema tem login, 2FA e validacao proprios.

Dev: Quando alguem clica para aprovar no dashboard, devo gravar o nome de um
usuario?

Domain expert: Nao. Isso e uma acao do operador local. O SOG sabe que houve
intervencao humana local, mas nao identifica uma pessoa pelo dashboard.

Dev: Para uma tarefa enviada ao PJe ou SISTJWEB, devo chamar o campo de criado
por?

Domain expert: Nao. Use origem da tarefa. Criado por parece usuario autenticado,
e o dashboard local nao tem isso.

Dev: Entao o SOG precisa auditar qual pessoa fez cada acao?

Domain expert: Nao no escopo atual. O SOG e uma ferramenta local assistida:
mantem rastreabilidade operacional e aprovacao humana, mas nao identidade
individual no dashboard.

Dev: O operador precisa instalar Node.js, npm, Docker ou Docker Desktop?

Domain expert: Nao. O SOG deve chegar como executavel pronto; essas dependencias
sao runtime interno ou devem ser eliminadas da jornada do operador.

Dev: Depois de preparar o runtime, o que o executavel deve entregar?

Domain expert: Uma instalacao local completa: baixar, configurar e iniciar o SOG
localmente, deixando ao operador apenas confirmar permissoes e usar o dashboard.

Dev: Electron deve ser o lugar permanente de configuracao e operacao?

Domain expert: Nao. Electron e apenas a casca local. Configuracao operacional
deve ser uma aba dentro do dashboard principal.

Dev: O que acontece com as configuracoes que hoje estao no Electron?

Domain expert: Elas devem ir para a aba de configuracao do dashboard principal.

Dev: Se Node.js, npm ou Docker CLI estiverem ausentes, o que o executavel faz?

Domain expert: Ele verifica a maquina, pede autorizacao na interface e continua
o preparo automatizado do runtime para instalar o SOG localmente.

Dev: Podemos usar Docker Desktop como caminho principal se ele ja estiver
instalado?

Domain expert: Nao. Docker Desktop exige interacao e conhecimento minimo. O SOG
deve preferir Docker CLI automatizado, sem depender da GUI.

Dev: E se o Windows exigir permissao de administrador?

Domain expert: O executavel pode pedir elevacao, mas deve explicar antes o que
sera instalado ou configurado.

Dev: E se o Windows nao tiver WSL instalado ou habilitado?

Domain expert: O executavel deve preparar isso por baixo, pedindo permissao. WSL
nao deve virar tarefa manual do operador.

Dev: E se o Windows precisar reiniciar para concluir WSL ou virtualizacao?

Domain expert: O SOG deve tratar isso como parte controlada da instalacao e
retomar depois, sem fazer o operador recomecar.

Dev: E se algo nao puder ser resolvido automaticamente?

Domain expert: O operador deve receber uma orientacao simples com telefone e
email de suporte. Os detalhes tecnicos devem ficar no diagnostico para suporte.

Dev: O comando npx e a jornada principal do operador?

Domain expert: Nao. Ele pode ser um atalho tecnico de distribuicao, mas a
jornada principal do operador leigo e abrir o executavel pronto.

Dev: Entao devemos manter rastreabilidade, mas remover conceitos de multiusuario
do dashboard?

Domain expert: Sim. O SOG precisa mostrar o que aconteceu e o que foi decidido,
sem modelar contas ou autenticacao do dashboard.

Dev: Devemos preservar um modo exposto no desenho atual?

Domain expert: Nao. Modo exposto esta fora do escopo atual; o SOG deve ser
modelado como ferramenta local assistida.

Dev: API e agente podem manter schemas proprios para os mesmos dados?

Domain expert: Nao. O contrato compartilhado deve ser canonico; API e agente nao
devem manter copias concorrentes da mesma linguagem de dados.

Dev: O schema SQL deve morar no agente porque ele executa a automacao?

Domain expert: Nao. O banco e compartilhado entre agente, API e dashboard; o
schema deve pertencer ao contrato compartilhado.

Dev: A API pode ter modelos proprios para uma tela especifica?

Domain expert: Sim, quando forem contratos de apresentacao da API. Eles podem
formatar ou agregar dados para o dashboard, mas nao redefinir o contrato
compartilhado.

Dev: O frontend pode criar modelos proprios?

Domain expert: Sim, como modelo de tela. Ele pode traduzir dados da API para
exibicao, mas nao criar uma fonte de verdade paralela.

Dev: Entao toda duplicacao deve ser removida?

Domain expert: Nao. Duplicacao de dominio deve ser removida. Apresentacao
especifica pode existir quando deixa claro que nao e fonte de verdade.

Dev: O problema de um modulo compartilhado grande e o tamanho do arquivo?

Domain expert: Nao. O problema e misturar fronteiras de dominio. Separar so faz
sentido quando deixa mais clara a linguagem de cada responsabilidade.

Dev: Separar fronteiras significa devolver regras para API ou agente?

Domain expert: Nao. O contexto compartilhado continua dono da linguagem comum;
ele so deve ser organizado por fronteiras de dominio.

Dev: Quais sao as fronteiras principais do contexto compartilhado?

Domain expert: Processos e aprovacao; agente e ciclos; tarefas e sessoes
externas; e infraestrutura de banco.

Dev: Tarefas operacionais sao excesso do MVP?

Domain expert: Nao. Elas sao parte do dominio atual quando representam trabalho
externo ou retomavel do SOG.

Dev: O operador deve gerenciar uma fila tecnica de tarefas?

Domain expert: Nao. O dashboard deve mostrar estado operacional necessario:
progresso, bloqueios e retomadas, nao uma administracao de jobs.

Dev: Playwright por sistema, transacoes SQLite e dashboard por secoes sao
excesso?

Domain expert: Nao. Eles tratam complexidade real: sistemas externos diferentes,
concorrencia local e visao operacional com muitas areas.
