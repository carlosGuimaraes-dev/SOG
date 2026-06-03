# Runtime Refactor Backend/Shared Evidence

Evidência durável para `SOGA-64`, reconciliando os artefatos backend/shared cobrados na auditoria da refatoração runtime.

## Artefatos recuperados no checkout compartilhado

- `agente/tests/test_auth_manager.py`
- `api/tests/test_shared_contracts.py`
- `agente/tests/test_shared_contracts.py`
- `agente/tests/test_emissao_idempotencia.py`
- `docs/processos/0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf`
- `shared/sog_shared/agente_ciclos.py`
- `shared/sog_shared/infra_db.py`
- `shared/sog_shared/processos_aprovacao.py`
- `shared/sog_shared/tarefas_sessoes.py`

## Supersessão explícita

- Item auditado: `shared/sog_shared/runtime_preparation.py`
- Estado atual: o bootstrap runtime é explícito e canônico em:
  - `sog_shared.config.init_config()`
  - `sog_shared.infra_db.init_db()`
- Evidência adicional: `shared/sog_shared/runtime_preparation.py` foi reintroduzido como shim fino de compatibilidade, sem side-effects no import, expondo `prepare_runtime()` para encadear ambos os passos de bootstrap.

## Cobertura focada associada

- `api/tests/test_shared_contracts.py`
  - garante reuso dos models compartilhados
  - garante que auth do dashboard não vazou para `shared`
  - garante schema canônico
  - garante que `runtime_preparation.prepare_runtime()` delega para `init_config()` e `init_db()`
- `agente/tests/test_shared_contracts.py`
  - garante que o agente reutiliza o schema compartilhado canônico
- `agente/tests/test_emissao_idempotencia.py`
  - garante persistência e reuso de evidências de emissão/anexação no fluxo backend/shared
- `agente/tests/test_extrator_pdf.py`
  - depende do fixture PDF real acima para a regressão focada rodar até o fim no checkout compartilhado
