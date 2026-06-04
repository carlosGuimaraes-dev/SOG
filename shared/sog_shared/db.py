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
from sog_shared.agente_ciclo_contadores import *  # noqa: F401,F403
from sog_shared.infra_db import *  # noqa: F401,F403
from sog_shared.processos_aprovacao import *  # noqa: F401,F403
from sog_shared.tarefas_sessoes import *  # noqa: F401,F403

ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ = "demonstrativo_emitido_sistj"
ETAPA_EVIDENCIA_ANEXO_PJE = "demonstrativo_anexado_pje"


class _InfraDbProxy:
    def __getattr__(self, name: str):
        if name == "get_conn":
            return get_conn
        if name == "init_db":
            return init_db
        return getattr(_infra_db, name)


_agente_ciclos.infra_db = _InfraDbProxy()
_recalcular_contadores_ciclo = _agente_ciclos._recalcular_contadores_ciclo


def salvar_credenciais_dashboard(usuario: str, senha: str) -> None:
    """Salva a credencial unica do dashboard."""
    with get_conn() as conn:
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
    with get_conn() as conn:
        row = conn.execute(
            "SELECT usuario, senha FROM dashboard_credenciais WHERE id = 1"
        ).fetchone()
        return dict(row) if row else None


def _obter_ciclo_mais_recente_do_processo_conn(conn, processo_id: int) -> Optional[str]:
    row = conn.execute(
        """
        SELECT m.ciclo_uuid
        FROM agente_ciclo_membros m
        JOIN agente_ciclos c ON c.uuid = m.ciclo_uuid
        WHERE m.processo_id = ?
        ORDER BY c.criado_em DESC, m.id DESC
        LIMIT 1
        """,
        (processo_id,),
    ).fetchone()
    if not row:
        return None
    return row["ciclo_uuid"]
