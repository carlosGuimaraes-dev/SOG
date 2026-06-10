# Checklist Tecnico: Autenticacao Externa Assistida

## Escopo aprovado

- Um unico CTA principal para autenticar PJe e SISTJWEB para o agente.
- Distincao explicita entre autenticar para o agente e abrir site externamente.
- Remocao das acoes ambíguas hoje exibidas como caminho principal.

## Mudancas de frontend

- Substituir a composicao atual de cards em [frontend/src/pages/Configuracao.tsx](frontend/src/pages/Configuracao.tsx) por:
  - um bloco principal de autenticacao assistida;
  - um painel de status por sistema;
  - acoes secundarias de abertura externa.
- Remover como acoes principais os botoes Abrir PJe, Abrir SISTJWEB e Solicitar reautenticacao.
- Manter abertura externa apenas como acao secundaria, com rotulo Abrir site externamente.
- Exibir passo a passo persistente durante o fluxo.
- Incluir polling curto de status enquanto a autenticacao estiver em andamento.
- Atualizar testes em [frontend/src/__tests__/Configuracao.test.tsx](frontend/src/__tests__/Configuracao.test.tsx) para cobrir:
  - CTA unico;
  - passo a passo visivel;
  - status independente por sistema;
  - ausencia dos botoes antigos como caminho principal.

## Integracao dashboard -> desktop

- Expor uma acao unica do dashboard para abrir o navegador de sessao do SOG.
- Reaproveitar o mecanismo hoje existente no desktop em [desktop/main.js](desktop/main.js), [desktop/preload.js](desktop/preload.js) e [desktop/lib/chrome-login.js](desktop/lib/chrome-login.js).
- Definir um contrato claro entre frontend e casca local:
  - abrir navegador de sessao;
  - informar sucesso ou erro de abertura;
  - permitir retomada sem duplicar janela.

## Mudancas no agente

- Parar de tratar o navegador monitoravel e o navegador operacional como sessoes distintas.
- Fazer o agente operar sobre a mesma sessao original do navegador do SOG, conforme a linguagem de [CONTEXT.md](CONTEXT.md).
- Revisar [agente/src/modulos/auth_manager.py](agente/src/modulos/auth_manager.py) e [agente/src/modulos/session_profile.py](agente/src/modulos/session_profile.py) para eliminar a abertura de um segundo perfil concorrente apos o login manual.
- Revisar [agente/src/servico.py](agente/src/servico.py) e [agente/src/modulos/chrome_login_capture.py](agente/src/modulos/chrome_login_capture.py) para que a validacao da sessao alimente diretamente a sessao usada pelo agente, e nao apenas um snapshot de compatibilidade sem consumo efetivo.

## API e estados

- Preservar a leitura independente de status por sistema em [api/src/rotas/dashboard.py](api/src/rotas/dashboard.py).
- Ajustar as mensagens para a nova linguagem operacional:
  - aguardando login no navegador do SOG;
  - sessao ativa;
  - falta concluir login no sistema pendente.
- Reavaliar se os endpoints atuais de reautenticacao continuam necessarios como acao principal.
- Se continuarem existindo, relegar seu uso a fluxo interno ou recuperacao tecnica, nao a CTA principal do operador.

## Remocoes obrigatorias

- Remover da UX principal a nocao de que abrir uma aba comum equivale a autenticar.
- Remover a necessidade de o operador escolher entre varios caminhos de login.
- Remover qualquer comportamento que abra outro Chromium depois de a sessao ja ter sido reconhecida.

## Ordem recomendada de implementacao

1. Ajustar integracao do dashboard com a casca local para disparar o navegador de sessao do SOG.
2. Unificar a sessao usada pelo agente com a sessao autenticada pelo operador.
3. Refatorar a tela de configuracao para o novo fluxo unico.
4. Atualizar contratos de status e mensagens.
5. Cobrir com testes de frontend, desktop e agente.

## Criterios de aceite

- Existe um unico CTA principal: Conectar PJe e SISTJWEB.
- O navegador aberto para login e o navegador de sessao do SOG.
- O dashboard exibe os tres passos curtos durante a autenticacao.
- O status passa automaticamente para sessao ativa sem abrir outro navegador.
- Quando apenas um sistema falhar, a interface mostra exatamente qual esta pendente.
- Os botoes antigos deixam de ser o caminho principal e o restante da superficie ambigua e removido.