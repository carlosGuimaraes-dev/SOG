# Uncle Bob Quality Audit - Breakdown para Paperclip

## Issue Mae

### Titulo
Remediar reprovacao do Uncle Bob Quality Audit

### Tipo
AFK

### Blocked by
None - can start immediately

### O que construir
Criar a trilha de remediacao do relatorio Uncle Bob Quality Audit para tirar o repositorio do estado `REPROVADO` ate que os hotspots criticos e a baseline operacional de qualidade estejam estabilizados.

### Acceptance criteria
- [ ] Todas as slices criticas do relatorio estao rastreadas a partir desta issue
- [ ] Existe uma ordem clara de execucao para sair do estado `REPROVADO`
- [ ] O progresso das remediacoes pode ser acompanhado sem depender do relatorio como checklist informal

## Slice 1

### Titulo
Refatorar Ciclo Atual para sair do vermelho de complexidade

### Tipo
AFK

### Blocked by
- Issue Mae

### O que construir
Refatorar a tela de ciclo atual como uma slice vertical que preserve o comportamento existente para o operador, mas que reduza a complexidade e o tamanho da implementacao ate sair do estado vermelho apontado pela auditoria.

### Acceptance criteria
- [ ] A tela de ciclo atual mantem o comportamento funcional existente para o operador
- [ ] A implementacao fica menor e mais testavel, reduzindo o hotspot destacado no relatorio
- [ ] Os testes e checks relevantes passam localmente e no CI

## Slice 2

### Titulo
Refatorar tela de Fila para reduzir complexidade e tamanho

### Tipo
AFK

### Blocked by
- Issue Mae

### O que construir
Refatorar a tela de fila como uma slice vertical preservando busca, navegacao, estados e acoes visiveis ao operador, enquanto a implementacao sai do estado vermelho de complexidade e tamanho indicado pela auditoria.

### Acceptance criteria
- [ ] A tela de fila mantem busca, navegacao e acoes sem regressao perceptivel
- [ ] O hotspot de complexidade/tamanho fica reduzido para fora do estado vermelho
- [ ] Os testes e checks relevantes passam localmente e no CI

## Slice 3

### Titulo
Fatiar extracao de sentenca em extratores testaveis por responsabilidade

### Tipo
AFK

### Blocked by
- Issue Mae

### O que construir
Quebrar a extracao de sentenca em partes menores, nomeadas por responsabilidade, preservando o comportamento ponta a ponta do agente ao interpretar os dados relevantes da sentenca.

### Acceptance criteria
- [ ] A extracao continua retornando os campos esperados sem regressao funcional
- [ ] A logica passa a ser organizada em unidades menores e testaveis por responsabilidade
- [ ] Os testes e checks relevantes passam localmente e no CI

## Slice 4

### Titulo
Quebrar preenchimento no SISTJWeb em etapas verificaveis

### Tipo
AFK

### Blocked by
- Issue Mae

### O que construir
Separar o fluxo de preenchimento no SISTJWeb em etapas verificaveis de navegacao, preenchimento e captura de resultado, mantendo o caminho completo de automacao funcionando do ponto de vista do agente.

### Acceptance criteria
- [ ] O fluxo de preenchimento continua funcionando ponta a ponta para o agente
- [ ] As responsabilidades ficam separadas em etapas menores e verificaveis
- [ ] Os testes e checks relevantes passam localmente e no CI

## Slice 5

### Titulo
Consolidar baseline obrigatoria de qualidade no CI do repositorio

### Tipo
AFK

### Blocked by
- Issue Mae

### O que construir
Consolidar a baseline operacional de qualidade do repositorio para que coverage, dependencias do frontend e feedback do workflow virem sinal continuo para as proximas iteracoes do Codex.

### Acceptance criteria
- [ ] O workflow de qualidade do repositorio esta alinhado com a auditoria aprovada
- [ ] O CI fornece feedback acionavel para refatoracoes e regresses futuras
- [ ] A baseline de qualidade pode ser usada como criterio objetivo nas proximas PRs

## Slice 6

### Titulo
Reduzir tamanho de modulos centrais apos estabilizar hotspots criticos

### Tipo
AFK

### Blocked by
- Slice 3
- Slice 4

### O que construir
Reduzir o tamanho estrutural dos modulos centrais ainda acima do limite apos a estabilizacao dos hotspots criticos, preservando o comportamento do agente e a rastreabilidade das regras de negocio.

### Acceptance criteria
- [ ] Os modulos centrais deixam de carregar o mesmo risco estrutural apontado no relatorio
- [ ] O comportamento atual continua protegido por testes e checks
- [ ] A mudanca e verificavel de forma independente apos as slices criticas anteriores
