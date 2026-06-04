"""
Facade de compatibilidade para o pacote compartilhado.

O código de domínio foi separado em módulos por fronteira:
  - processos_aprovacao
  - agente_ciclos
  - tarefas_sessoes
  - infra_db
"""

from typing import Any, Dict, Optional

import sog_shared.agente_ciclos as _agente_ciclos
from sog_shared import infra_db as _infra_db
from sog_shared.agente_ciclos import *  # noqa: F401,F403
from sog_shared.infra_db import *  # noqa: F401,F403
from sog_shared.processos_aprovacao import *  # noqa: F401,F403
from sog_shared.tarefas_sessoes import *  # noqa: F401,F403
from sog_shared.agente_ciclos import (  # noqa: F401
    _obter_ciclo_mais_recente_do_processo_conn,
)

ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ = "demonstrativo_emitido_sistj"
ETAPA_EVIDENCIA_ANEXO_PJE = "demonstrativo_anexado_pje"


def _current_get_conn():
    return globals()["get_conn"]


def _current_init_db():
    return globals()["init_db"]


class _InfraDbProxy:
    def __getattr__(self, name: str):
        if name == "get_conn":
            return _current_get_conn()
        if name == "init_db":
            return _current_init_db()
        return getattr(_infra_db, name)


_agente_ciclos.infra_db = _InfraDbProxy()
_recalcular_contadores_ciclo = _agente_ciclos._recalcular_contadores_ciclo


def salvar_credenciais_dashboard(usuario: str, senha: str) -> None:
    with _current_get_conn()() as conn:
        conn.execute(
            """
            INSERT INTO dashboard_credenciais (id, usuario, senha, atualizado_em)
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                usuario = excluded.usuario,
                senha = excluded.senha,
                atualizado_em = CURRENT_TIMESTAMP
            """,
            (usuario, senha),
        )
        conn.commit()


def obter_credenciais_dashboard() -> Optional[Dict[str, Any]]:
    with _current_get_conn()() as conn:
        row = conn.execute(
            "SELECT usuario, senha FROM dashboard_credenciais WHERE id = 1"
        ).fetchone()
        return dict(row) if row else None
