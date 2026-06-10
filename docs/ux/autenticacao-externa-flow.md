# Flow Spec: Autenticacao Externa Assistida

## Objetivo do fluxo

Substituir a superficie atual de autenticacao por um fluxo unico, guiado e coerente com a sessao realmente usada pelo agente.

## Estrutura da tela

### Bloco principal

Titulo: Conexao com sistemas externos

Texto de apoio: Conecte PJe e SISTJWEB no navegador de sessao do SOG. O agente reutiliza essa mesma sessao para operar.

CTA principal: Conectar PJe e SISTJWEB

Estado do CTA:

- Padrao: habilitado.
- Em andamento: Abrindo navegador de sessao...
- Sucesso: Sistemas conectados.
- Erro: Nao foi possivel abrir o navegador de sessao.

### Passo a passo persistente

1. Entre no PJe.
2. Entre no SISTJWEB.
3. Aguarde validacao automatica.

### Painel de status por sistema

PJe:

- Aguardando login
- Sessao ativa
- Falha na validacao

SISTJWEB:

- Aguardando login
- Sessao ativa
- Falha na validacao

Regra:

- O status deve ser independente por sistema.
- A mensagem deve indicar explicitamente o pendente atual.

### Acoes secundarias permitidas

Rotulo: Abrir site externamente

Uso:

- Serve apenas para revisao manual fora do fluxo operacional do agente.
- Deve ficar visualmente secundaria em relacao ao CTA principal.

## Conteudo que deve ser removido

- Remover o par de acoes principais por card: Abrir PJe e Solicitar reautenticacao.
- Remover o par de acoes principais por card: Abrir SISTJWEB e Solicitar reautenticacao.
- Remover qualquer texto que sugira que abrir uma aba comum equivale a autenticar para o agente.
- Remover a necessidade de o operador decidir entre varios caminhos de login.

## Regras de comportamento

- O CTA principal deve abrir o navegador de sessao do SOG, nao o navegador padrao generico.
- O agente nao deve abrir outro Chromium apos a autenticacao ja detectada.
- A tela deve atualizar automaticamente o status quando cada sessao externa for reconhecida.
- Se apenas um sistema estiver autenticado, a tela deve apontar apenas o sistema pendente.
- O status final so muda para concluido quando PJe e SISTJWEB estiverem ativos.

## Estados de interface

### Estado inicial

- CTA principal visivel.
- Passos visiveis.
- Ambos os sistemas como aguardando login.

### Estado em progresso

- CTA principal desabilitado.
- Mensagem: Validando sessoes abertas no navegador do SOG.
- Indicadores independentes por sistema.

### Estado de sucesso

- Mensagem principal: Sistemas conectados. O agente pode continuar.
- PJe e SISTJWEB marcados como sessao ativa.

### Estado de falha parcial

- Mensagem principal: Falta concluir o login no sistema pendente.
- Destaque apenas do sistema faltante.
- CTA principal pode mudar para Retomar autenticacao.

### Estado de erro tecnico

- Mensagem principal: Nao foi possivel validar a sessao no navegador do SOG.
- Acao de recuperacao: Tentar novamente.
- Diagnostico tecnico permanece secundario, nunca como instrucao principal.

## Principios de design

- Um fluxo principal por objetivo.
- Linguagem operacional, nao tecnica.
- Feedback automatico e incremental.
- Separacao explicita entre autenticar para o agente e abrir um site externamente.

## Requisitos de acessibilidade

- O CTA principal deve ser o primeiro foco acionavel da secao.
- O passo a passo deve ser lido em ordem logica por leitor de tela.
- Mudancas de status devem ser anunciadas por regiao viva.
- Cada sistema deve combinar cor e texto, nunca cor sozinha.
- Estados de carregamento precisam de texto descritivo, nao apenas spinner.