# Auditoria no-overengineering para elicitação futura

Data: 2026-06-02

## Objetivo

Registrar os pontos do projeto SOG que parecem excesso de engenharia ou
complexidade justificada, à luz do PRD atual, para uma futura rodada de
elicitação antes de executar qualquer corte.

Este documento não autoriza implementação automática. Ele serve para orientar
perguntas, decisões de escopo e fatiamento de trabalho.

## Estado publicado

- `sogtj@0.1.8` publicado no npm.
- Instalador Windows `0.1.5` publicado no R2:
  `https://sog.carlosguimaraes.us/sogtj/v0.1.5/SOG.Desktop.Setup.0.1.5.exe`
- SHA256 validado:
  `552bd7afdf8feb0cd59d44f435013e4a4214a71a62ee09c018e3d67df377ff5c`
- `npx -y sogtj@latest --dry-run` aponta para o instalador `0.1.5`.

## Núcleo do PRD

O sistema existe para:

1. Monitorar processos no PJe/TJDFT.
2. Consultar e extrair dados via Datajud, PJe e PDF.
3. Preencher custas no SISTJWEB.
4. Pausar para aprovação humana no dashboard.
5. Após aprovação, emitir Demonstrativo e anexar no PJe.

Tecnologias assumidas pelo PRD:

- Agente Python com Playwright.
- FastAPI para o dashboard.
- React para o dashboard.
- SQLite compartilhado.
- Docker Compose.
- SOG Desktop/Electron para operador Windows leigo.

## Regras de simplicidade aplicadas

- Login manual no PJe/SISTJWEB é requisito essencial, não excesso.
- Login próprio do dashboard local desktop é fricção removível quando o acesso
  fica preso a `127.0.0.1`.
- Preferir uma fonte de verdade para schema, modelos e regras.
- Não criar repository/service/factory para consertar duplicação; primeiro
  deletar ou consolidar.
- Aceitar complexidade quando há concorrência real, fronteira pública ou
  domínio externo instável.

## Candidatos a overengineering

### 1. Duplicação de schema e modelos

Arquivos envolvidos:

- `api/src/schemas.py`
- `shared/sog_shared/schemas.py`
- `agente/src/banco/schema.sql`
- `shared/sog_shared/schema.sql`

Por que questionar:

- O PRD precisa de um contrato coerente entre agente, API e dashboard.
- Duas fontes de verdade tornam migração e revisão mais caras.
- O risco não é Big-O; é divergência silenciosa.

Perguntas de elicitação:

- Qual arquivo deve ser a fonte canônica: `shared/sog_shared/*`?
- `api/src/schemas.py` pode virar reexport simples ou ainda tem contrato
  específico da API?
- `agente/src/banco/schema.sql` ainda é usado em runtime ou só sobrou de legado?

### 2. `shared/sog_shared/db.py` concentrando responsabilidades

Arquivo envolvido:

- `shared/sog_shared/db.py`

Por que questionar:

- O arquivo está grande e mistura schema/migração, queries de processo, ciclo,
  tarefas e reprocessamento.
- Criar uma camada repository seria trocar um excesso por outro.
- O primeiro corte deve ser remover duplicatas e funções sem uso, depois avaliar
  se separar por domínio reduz risco real.

Perguntas de elicitação:

- Quais funções são usadas pelo agente?
- Quais funções são usadas somente pela API?
- Existe código morto de fluxos antigos?
- Separar por arquivos simples (`processos.py`, `ciclos.py`, `tarefas.py`) ajuda
  ou só espalha o problema?

### 3. Autenticação JWT completa fora do modo exposto

Arquivos envolvidos:

- `api/src/auth.py`
- `api/src/rotas/auth.py`
- `shared/sog_shared/schema.sql` (`refresh_tokens`)
- `frontend/src/lib/auth.tsx`

Por que questionar:

- Para SOG Desktop local, o dashboard roda em localhost e sem login próprio.
- JWT, refresh token e tabela de refresh são justificáveis apenas para execução
  manual/exposta.

Perguntas de elicitação:

- O dashboard será exposto em rede/VPS no escopo atual?
- Se não for exposto, a autenticação completa deve ficar como modo opcional ou
  sair do MVP?
- Quem é o dono humano do requisito de login do dashboard fora do desktop?

### 4. Fila/tarefas assíncronas possivelmente acima do MVP

Arquivos envolvidos:

- `api/src/rotas/tarefas.py`
- funções de `agente_tarefas` em `shared/sog_shared/db.py`
- telas/status relacionados no frontend

Por que questionar:

- O PRD descreve ciclo operacional e aprovação humana.
- Uma fila de tarefas detalhada pode ser necessária para retomada/reprocesso,
  mas também pode estar modelando mais estados do que o operador precisa ver.

Perguntas de elicitação:

- O operador precisa manipular tarefas individualmente?
- A fila é requisito para reautenticação PJe/SISTJWEB ou apenas conveniência?
- O ciclo/lote persistido cobre o caso sem uma camada de tarefas separada?

### 5. Tipos e modelos repetidos no frontend

Arquivos envolvidos:

- `frontend/src/types/processo.ts`
- interfaces locais em páginas como `CicloAtual.tsx` e `Fila.tsx`

Por que questionar:

- Tipos locais são bons quando reduzem acoplamento.
- Repetição de contratos de API em várias páginas aumenta drift.

Perguntas de elicitação:

- Quais tipos representam resposta de API e devem ser compartilhados?
- Quais tipos são apenas view-model local e devem permanecer locais?

## Complexidade justificada

### Login manual PJe/SISTJWEB

Justificativa:

- Sem login do usuário no PJe/SISTJWEB, o sistema não opera.
- SSO/2FA impedem armazenamento simples de credenciais.
- Navegador visível e persistente, com tempo real para 2FA, é complexidade de
  domínio; copiar `storage_state` para outro navegador é mecanismo frágil a
  remover.

### Playwright modularizado por sistema

Justificativa:

- PJe e SISTJWEB têm fluxos, seletores, downloads e timeouts diferentes.
- Uma classe/base comum mínima pode evitar repetição de browser/session.
- Não justificar camadas adicionais sem segunda implementação concreta.

### SQLite compartilhado com transações

Justificativa:

- API e agente podem tocar o mesmo banco.
- `BEGIN IMMEDIATE` evita corrida em aprovação, reprocessamento e ciclo.
- A complexidade é de concorrência real.

### Dashboard React com componentes por seção

Justificativa:

- O detalhe do processo tem muitas áreas: documentos, valores, logs,
  compensações, sucumbentes, screenshots e ações.
- Componentes pequenos ajudam leitura se não duplicarem contrato.

### Electron + runtime interno

Justificativa:

- O público-alvo é operador Windows leigo.
- O executável precisa esconder terminal, Node.js, npm, Docker CLI, WSL, Docker
  Compose e caminhos locais.
- Docker Desktop não é via operacional do usuário final.
- O `npx` pequeno + R2 pode continuar como atalho técnico de distribuição, mas
  não é a jornada principal do operador.

## Ordem sugerida para elicitação

1. Confirmar modos de operação: desktop local apenas, ou também dashboard exposto.
2. Definir fonte canônica para schema/modelos.
3. Mapear uso real de `shared/sog_shared/db.py`.
4. Decidir se tarefas assíncronas são núcleo do MVP ou suporte interno.
5. Consolidar tipos frontend apenas onde houver contrato de API repetido.

## Critério de aceite para execução futura

Antes de implementar qualquer corte, a elicitação deve produzir:

- Dono humano de cada requisito mantido.
- Lista explícita do que será deletado, mantido ou adiado.
- Testes mínimos que provam que o fluxo PJe/SISTJWEB, aprovação humana e
  instalação desktop continuam funcionando.
- Confirmação de que nenhuma senha de PJe/SISTJWEB será armazenada.

## Elicitação aprovada

Data de aprovação: 2026-06-02

Dono humano das decisões: Carlos Guimarães.

Esta seção consolida a elicitação aprovada para servir como base de PRD antes da
refatoração. A decisão central é que o SOG é uma ferramenta local assistida para
operador Windows leigo, não um sistema multiusuário auditável nem um dashboard
exposto.

### Linguagem canônica

Ver `CONTEXT.md` para as definições aprovadas. Os termos que guiam o PRD são:

- Ferramenta local assistida.
- Executável pronto.
- Casca local.
- Dashboard local.
- Aba de configuração.
- Login manual externo.
- Navegador de sessão do SOG.
- Abertura assistida de sistema externo.
- Abertura independente por sistema.
- Runtime interno.
- Preparo automatizado do runtime.
- Docker CLI automatizado.
- WSL interno.
- Contrato compartilhado.
- Banco compartilhado.
- Fronteira de domínio.
- Tarefa operacional.
- Estado operacional.

### Implementar

- Dashboard principal como experiência operacional única, incluindo uma aba de
  configuração.
- Electron apenas como casca local para preparo de runtime, instalação local e
  abertura do dashboard.
- Executável pronto que verifica Node.js, npm, Docker CLI e WSL; quando faltar
  algo, pede autorização na interface e continua o preparo automatizado.
- Elevação/UAC explicada quando o Windows exigir permissão para instalar ou
  configurar runtime interno.
- Retomada após reinicialização quando Windows 11 exigir reboot para WSL,
  virtualização ou runtime de containers.
- Diagnóstico para suporte com orientação simples para operador e dados de
  contato como telefone e email.
- Login PJe/SISTJWEB em navegador de sessão do SOG, visível e persistente.
- Botões separados e independentes na aba de configuração para abrir PJe e
  SISTJWEB.
- Validação independente de sessão ativa em PJe e SISTJWEB.
- Agente trabalhando na mesma sessão/perfil em que o operador fez login, sem
  copiar sessão para outro navegador.
- `shared/sog_shared` como fonte canônica do contrato compartilhado e do schema
  do banco compartilhado.
- Contratos de apresentação da API apenas quando agregam ou formatam dados para
  uma rota/tela.
- Modelos de tela no frontend apenas para apresentação visual, sem redefinir
  domínio nem contrato da API.
- Organização do contexto compartilhado por fronteiras de domínio: processos e
  aprovação; agente e ciclos; tarefas e sessões externas; infraestrutura de
  banco.
- Dashboard mostrando estado operacional necessário, não uma fila técnica
  gerenciável pelo operador.

### Deletar

- Login/autenticação própria do dashboard local.
- JWT, refresh token e tabela de refresh ligados ao dashboard.
- Conceitos multiusuário do dashboard.
- Auditoria por usuário autenticado no dashboard.
- Painel/configurador operacional próprio do Electron.
- Jornada baseada em Docker Desktop.
- Checklist manual de Node.js, npm, Docker, Docker Compose ou WSL para operador.
- Cópias concorrentes de schema/modelos de domínio em `api/` e `agente/`.
- `storage_state` como mecanismo principal de transferência de sessão externa.
- Abertura de múltiplas instâncias efêmeras de Chromium que fecham antes do 2FA.
- Botão único/acoplado para login simultâneo em PJe e SISTJWEB.
- Campo/conceito `criado_por` quando ele representar usuário autenticado do
  dashboard; usar origem da tarefa.

### Manter

- Login manual externo em PJe e SISTJWEB.
- 2FA com tempo humano real.
- Playwright separado por sistema externo quando fluxos, seletores, downloads e
  timeouts forem diferentes.
- SQLite compartilhado com transações para aprovação, ciclo e retomada.
- Tarefas operacionais como domínio atual.
- Rastreabilidade operacional.
- Dashboard por seções/componentes, desde que não duplique contrato de domínio.
- `npx`/R2 como atalho técnico de distribuição, não como jornada principal do
  operador.

### Postergar

- Modo exposto/remoto.
- Multiusuário.
- Auditoria por pessoa.
- Administração técnica de fila pelo operador.
- Docker Desktop como jornada operacional.
- Capturar Chrome comum já aberto fora do controle do SOG.
- Abstrações adicionais de Playwright sem segunda implementação concreta.
- ADR formal desta decisão. A aprovação atual deve primeiro virar PRD.

### Oportunidades arquiteturais

Relatório visual gerado em:

`/private/tmp/architecture-review-20260602-213457.html`

Top recommendation: começar pelo módulo Navegador de sessão do SOG. Ele remove o
ponto falho atual, que é copiar sessão para outro navegador, e concentra a
complexidade real do login manual externo em uma interface pequena: abrir PJe,
abrir SISTJWEB, validar sessões e operar na sessão original.

Candidatos levantados:

1. Aprofundar o módulo Navegador de sessão do SOG.
2. Mover Configuração operacional para uma aba do Dashboard local.
3. Tornar `shared/sog_shared` o módulo profundo de Contrato compartilhado.
4. Separar a implementação do banco compartilhado por Fronteira de domínio.

### Recomendações arquiteturais para implementação

Estas recomendações vêm da skill `improve-codebase-architecture` e devem entrar
no PRD como orientação de refatoração. Elas não definem interfaces finais; a
próxima etapa deve transformar cada recomendação em requisitos e critérios de
aceite.

#### 1. Aprofundar o módulo Navegador de sessão do SOG

Recomendação: **Strong**.

Objetivo:

- Concentrar abertura, validação e uso da sessão externa em um módulo profundo.
- Eliminar a coreografia frágil de Chrome CDP + cópia de `storage_state` + novo
  navegador Playwright.

Arquivos/módulos envolvidos:

- `agente/src/modulos/auth_manager.py`
- `agente/src/modulos/chrome_login_capture.py`
- `agente/src/servico.py`
- `desktop/lib/chrome-login.js`
- `desktop/main.js`
- futura aba de configuração no dashboard

Mudança arquitetural:

- O dashboard oferece ações independentes para abrir PJe e SISTJWEB.
- O SOG abre um navegador visível, persistente e controlado pelo SOG.
- O operador faz login e 2FA nesse navegador, sem pressa e sem fechamento
  automático.
- O agente valida e opera na mesma sessão original.
- O fluxo deixa de exportar/importar `storage_state` como mecanismo principal.

Teste de deleção:

- Se `chrome_login_capture.py` e o fluxo de cópia de sessão forem removidos, a
  complexidade não deve reaparecer em vários chamadores; ela deve ficar atrás do
  módulo Navegador de sessão do SOG.

Critérios de conclusão:

- PJe e SISTJWEB podem ser abertos separadamente.
- A validação de um sistema não bloqueia a do outro.
- O operador consegue concluir 2FA sem timeout imposto pelo SOG.
- O agente opera na sessão original.
- Nenhuma senha externa é armazenada.

#### 2. Mover Configuração operacional para o Dashboard local

Recomendação: **Strong**.

Objetivo:

- Transformar Electron em Casca local, não em painel operacional.
- Fazer a configuração permanente do SOG viver como aba dentro do dashboard
  principal.

Arquivos/módulos envolvidos:

- `desktop/main.js`
- `desktop/lib/config-merge.js`
- `frontend/src/App.tsx`
- futuras rotas/API de configuração
- futuros componentes da aba de configuração

Mudança arquitetural:

- Electron prepara runtime, inicia a instalação local e abre o dashboard.
- A configuração operacional migra para a aba de configuração do dashboard.
- A UI do Electron deixa de ser uma segunda superfície operacional.
- Mensagens de suporte e diagnóstico ficam acessíveis ao operador no fluxo do
  dashboard.

Teste de deleção:

- Se o painel/configurador do Electron for removido, a operação do SOG não deve
  perder uma superfície; ela deve existir no dashboard.

Critérios de conclusão:

- O operador configura o SOG pelo dashboard principal.
- Electron não expõe painel operacional próprio.
- A aba de configuração contempla abertura de PJe/SISTJWEB, status de runtime e
  diagnóstico de suporte.

#### 3. Tornar `shared/sog_shared` o Contrato compartilhado canônico

Recomendação: **Strong**.

Objetivo:

- Remover fontes concorrentes de schema/modelos.
- Fazer agente, API, dashboard e testes dependerem da mesma linguagem de dados.

Arquivos/módulos envolvidos:

- `shared/sog_shared/schema.sql`
- `shared/sog_shared/schemas.py`
- `api/src/schemas.py`
- `agente/src/banco/schema.sql`
- tipos/modelos locais do frontend
- testes que hoje apontam para schema do agente

Mudança arquitetural:

- `shared/sog_shared` passa a ser a fonte canônica do Banco compartilhado e dos
  modelos compartilhados.
- API mantém apenas contratos de apresentação quando agregam ou formatam dados
  para uma rota/tela.
- Frontend mantém apenas modelos de tela, sem redefinir domínio ou contrato da
  API.
- Testes usam o schema canônico do compartilhado.

Teste de deleção:

- Se `agente/src/banco/schema.sql` e modelos duplicados de domínio em `api/`
  forem removidos, a linguagem comum deve continuar disponível em
  `shared/sog_shared`, sem reaparecer como cópia local.

Critérios de conclusão:

- Há uma única fonte SQL canônica.
- Testes de API/agente usam o schema compartilhado.
- `api/src/schemas.py` não redefine modelos compartilhados.
- Tipos frontend duplicados viram modelo de tela ou são removidos.

#### 4. Organizar o banco compartilhado por Fronteira de domínio

Recomendação: **Worth exploring**.

Objetivo:

- Reduzir mistura de responsabilidades em `shared/sog_shared/db.py` sem criar
  camada repository ou abstração especulativa.
- Preservar o Contexto compartilhado como dono da linguagem comum.

Arquivos/módulos envolvidos:

- `shared/sog_shared/db.py`
- futuros módulos simples dentro de `shared/sog_shared`
- rotas em `api/src/rotas/*`
- chamadores do agente

Mudança arquitetural:

- Separar a implementação por fronteiras já aprovadas:
  - processos e aprovação;
  - agente e ciclos;
  - tarefas e sessões externas;
  - infraestrutura de banco.
- Manter interfaces simples, orientadas ao domínio, sem classes/repositories para
  uma única fonte de dados.
- Remover funções mortas antes de separar arquivos.

Teste de deleção:

- Se uma separação proposta só mover chamadas de lugar e exigir o mesmo
  conhecimento dos chamadores, ela deve ser rejeitada.
- Se a separação concentrar regras e testes por fronteira de domínio, ela é
  válida.

Critérios de conclusão:

- Mudanças em ciclos não exigem navegar por implementação de aprovação.
- Mudanças em tarefas/sessões externas não exigem entender processos.
- Infraestrutura de banco não carrega linguagem de processo, agente ou tarefa.
- Testes cobrem as interfaces das fronteiras, não detalhes internos de SQL.

### Testes mínimos esperados

- O dashboard local abre sem login próprio e sem redirecionar para `/login`.
- As rotas do dashboard não exigem JWT/refresh token.
- A aba de configuração abre PJe e SISTJWEB por botões independentes.
- O operador consegue fazer login e 2FA em cada sistema sem o navegador fechar.
- A validação de sessão de PJe não depende da validação de SISTJWEB, e vice-versa.
- O agente usa a sessão original do navegador de sessão do SOG.
- Nenhuma senha de PJe/SISTJWEB é armazenada.
- O executável detecta ausência de Node.js, npm, Docker CLI e WSL e pede
  autorização antes de preparar dependências.
- Falhas de preparo do runtime geram diagnóstico para suporte com telefone/email.
- O schema canônico usado por API, agente e testes vem de `shared/sog_shared`.
- Contratos de apresentação da API e modelos de tela não redefinem domínio.
- A aprovação humana e a retomada de ciclo continuam funcionando.
