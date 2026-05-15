"""
Rotas de histórico de processos emitidos/rejeitados.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "agente" / "src"))

from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from auth import get_current_user
from banco import db

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("", response_model=List[Dict[str, Any]])
def historico(
    limit: int = 50,
    offset: int = 0,
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT p.*, d.polo_ativo, d.valor_total_recolher, d.obs_operador
               FROM processos p
               LEFT JOIN dados_processo d ON d.processo_id = p.id
               WHERE p.status IN ('emitido', 'rejeitado')
               ORDER BY p.atualizado_em DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
