# MEMORY — QA

> Arquivo dinâmico. Registre padrões de bugs recorrentes, configurações
> de ambiente de teste e aprendizados sobre o comportamento do sistema.

---

## Configuração do ambiente de testes

<!-- Como rodar os testes neste projeto.
Exemplo:
- Comando: `pytest tests/ -v --cov=src`
- Requer: banco de teste em .env.test
- Fixtures principais: `db_session` (conftest.py), `auth_client` (conftest.py)
- Mocks necessários: serviço de email (mockado por padrão em tests/)
-->

_Não configurado ainda._

---

## Padrões de bugs recorrentes

<!-- Tipos de problemas que aparecem com frequência neste projeto.
Exemplo:
- Validações de input retornam 500 em vez de 400 quando o campo é null
- Endpoints de listagem não aplicam filtro de tenant em queries aninhadas
- Testes falham aleatoriamente quando rodados em paralelo (race condition
  no banco de teste compartilhado)
-->

_Nenhum padrão registrado ainda._

---

## Áreas de risco identificadas

<!-- Partes do sistema que historicamente têm mais bugs ou menos cobertura.
Exemplo:
- Módulo de notificações: cobertura < 30%, bugs frequentes
- Lógica de permissões: complexa, muitos edge cases
- Integração com API externa de pagamento: frágil, dependente de sandbox
-->

_Nenhuma área de risco registrada ainda._

---

## Histórico de validações

<!-- Registro das validações realizadas.
Exemplo:
- 2024-01-20: auth/jwt.py — APROVADO (cobertura 87%)
- 2024-01-22: routers/users.py — REPROVADO (Bug #3: DELETE sem verificação de owner)
- 2024-01-23: routers/users.py (v2) — APROVADO após correção
-->

_Nenhuma validação registrada ainda._
