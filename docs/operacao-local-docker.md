# Operação local em Docker

Este documento descreve o que o repositório entrega hoje e explicita onde a
implementação ainda diverge da arquitetura desejada.

## Serviços do Compose principal

- `agente`
- `api`
- `frontend`
- `nginx`

O `nginx` é o ponto de entrada do ambiente principal. Em desenvolvimento existe
também `docker-compose.dev.yml`, com Vite exposto em `localhost:3001` e nginx em
`localhost:8080`.

## Estado implementado hoje

### API e frontend

- A API sobe com healthcheck local em `http://localhost:8000/health` dentro do container.
- O frontend sobe em container separado e é consumido via nginx.
- A autenticação do dashboard usa cookies `httpOnly`.

### Agente

- O código do serviço longo existe em `agente/src/servico.py`.
- O container publicado ainda inicializa `supercronic` com `CMD ["supercronic", "/app/crontab"]`.
- O crontab roda a entrada empacotada do agente; portanto, a documentação não
  deve afirmar que a migração para serviço longo puro já foi concluída.

### Banco e arquivos

- `./dados` é montado em `agente` e `api`.
- O SQLite compartilhado fica em `/dados/custas.db`.
- Screenshots e demonstrativos também usam `./dados`.

## Fluxo operacional confirmado

1. Subir o Compose.
2. Acessar o dashboard.
3. Fazer login com as credenciais da API.
4. Acionar o agente pelo dashboard.
5. A API grava comandos em `agente_controle`.
6. O agente atualiza `agente_controle`, `agente_ciclos`, `agente_ciclo_membros`
   e demais tabelas operacionais ao processar ciclos e tarefas.

## Login interativo e `storage_state`

O código usa `storage_state` do Playwright para PJe e SISTJWEB, mas há um ponto
que precisa ser tratado com cuidado:

- o caminho default vem de `Path.home() / ".sog" / "auth"`
- o Compose atual não documenta nem monta um volume dedicado para esse diretório

Então a existência do mecanismo é confirmada pelo código, mas a persistência
entre rebuilds não deve ser prometida sem validação adicional.

## Limitações confirmadas

- Não documente credenciais de PJe ou SISTJWEB em `.env`; o fluxo é interativo.
- Não trate `docs/regras_custas_tjdft.md` como regra homologada de cálculo.
- Não assuma que `PRD.md` ou `SYMPHONY.md` representam o estado atual do runtime.

## Direção arquitetural ainda aberta

O alvo declarado no projeto continua sendo um agente controlado pelo dashboard
como serviço longo no container. O repositório já contém boa parte dessa lógica,
mas o bootstrap atual ainda depende de `supercronic` e `agente/crontab`.
