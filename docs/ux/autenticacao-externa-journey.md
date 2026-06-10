# Jornada: Autenticacao Externa Assistida

## Persona

- Quem: operador do SOG em desktop local.
- Objetivo: autenticar PJe e SISTJWEB para liberar a operacao do agente.
- Contexto: inicio do turno, retomada apos expiracao ou volta de pausa.
- Sinal de sucesso: a tela exibe sessao ativa nos dois sistemas e o agente nao reabre outro navegador.

## Etapa 1: Identificacao da necessidade

O que o operador faz: entra na aba de configuracao porque o agente esta aguardando login.

O que pensa: preciso conectar os sistemas para o agente voltar a funcionar.

O que sente: pressa e cautela, porque um erro aqui paralisa o fluxo.

Pontos de atrito atuais:

- Ha botoes demais para a mesma tarefa.
- Nao fica claro qual acao autentica de verdade para o agente.

Oportunidade:

- Um unico CTA principal, com rotulo operacional inequívoco: Conectar PJe e SISTJWEB.

## Etapa 2: Inicio da autenticacao

O que o operador faz: clica no CTA principal.

O que pensa: o sistema vai abrir o navegador certo para eu entrar.

O que sente: confianca moderada, desde que a instrucao seja objetiva.

Pontos de atrito atuais:

- O operador pode acabar no navegador comum e acreditar que concluiu o trabalho.

Oportunidade:

- Abrir apenas o navegador de sessao do SOG e mostrar o passo a passo curto na propria tela.

## Etapa 3: Login manual externo

O que o operador faz: realiza login e 2FA no PJe e no SISTJWEB.

O que pensa: entrei no primeiro sistema, falta o segundo, depois o SOG deve validar sozinho.

O que sente: atencao dividida entre o navegador e o dashboard.

Pontos de atrito atuais:

- Nao ha feedback claro de progresso por sistema.
- O operador nao sabe se precisa voltar e clicar em mais alguma coisa.

Oportunidade:

- Exibir progresso textual simples:
  1. Entre no PJe.
  2. Entre no SISTJWEB.
  3. Aguarde validacao automatica.

## Etapa 4: Validacao automatica

O que o operador faz: aguarda a deteccao do login.

O que pensa: o sistema precisa reconhecer minha sessao sem me pedir outro navegador.

O que sente: expectativa; qualquer nova janela gera perda de confianca.

Pontos de atrito atuais:

- O agente pode abrir outro Chromium e invalidar a expectativa do operador.

Oportunidade:

- Atualizacao automatica do status por sistema, sem nova janela.

## Etapa 5: Retomada operacional

O que o operador faz: confirma que ambos os sistemas estao ativos e volta ao trabalho.

O que pensa: agora o agente pode seguir.

O que sente: alivio e previsibilidade.

Sucesso:

- PJe ativo.
- SISTJWEB ativo.
- Mensagem final: Sistemas conectados. O agente pode continuar.

Falha parcial:

- Se apenas um sistema estiver pendente, a tela destaca somente ele.
- A acao secundaria permitida passa a ser Abrir site, apenas para revisao manual.