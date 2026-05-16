"""
Rotas de histórico de processos emitidos/rejeitados.
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import List

from auth import get_current_user
from sog_shared import db
from limiter import limiter
from schemas import HistoricoItemResponse

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("", response_model=List[HistoricoItemResponse])
@limiter.limit("30/minute")
def historico(
    request: Request,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
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
