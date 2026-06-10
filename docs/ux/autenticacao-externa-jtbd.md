# JTBD: Autenticacao Externa Assistida

## Premissas desta analise

- Persona principal: operador do SOG em ferramenta local assistida.
- Ambiente principal: desktop, com baixa tolerancia a fluxos tecnicos ambíguos.
- Contexto de uso: inicio da operacao do dia, retomada apos expiracao de sessao ou exigencia de 2FA.
- Consequencia da falha: agente parado, retrabalho operacional e duvida sobre qual sessao esta valendo.

## Job Statement

Quando eu preciso operar o SOG com PJe e SISTJWEB, quero autenticar os dois sistemas externos em um fluxo unico e guiado, para que o agente continue trabalhando na mesma sessao sem abrir outro navegador nem me obrigar a repetir o login.

## Solucao atual e dores

- Atual: a aba de configuracao exibe botoes independentes que parecem ser botoes de login, mas abrem o navegador comum.
- Atual: existe outro fluxo, no desktop, que abre o navegador monitoravel do SOG.
- Atual: o operador precisa deduzir sozinho qual botao realmente alimenta a sessao do agente.

## Principais dores

- Ambiguidade entre abrir o site e autenticar para o agente.
- Sensacao de erro porque o login parece ter funcionado, mas o agente abre outro Chromium depois.
- Falta de feedback claro sobre qual sistema ainda esta pendente.
- Excesso de acoes na tela para uma tarefa que deveria ter um unico caminho principal.

## Resultado desejado

- Um unico CTA principal para autenticar PJe e SISTJWEB para o agente.
- O navegador aberto para login e o mesmo navegador reaproveitado pelo agente.
- O operador entende em segundos o que fazer, em que ordem e quando terminou.
- A tela informa com precisao se o pendente e PJe, SISTJWEB ou ambos.

## Criterios de sucesso

- O operador inicia autenticacao sem precisar distinguir conceitos tecnicos como CDP, perfil ou storage state.
- A autenticacao de ambos os sistemas e concluida sem abertura de um segundo navegador pelo agente.
- O status da tela muda automaticamente para sessao ativa quando os dois sistemas forem detectados.
- Em caso de falha parcial, a interface informa apenas o proximo passo necessario.