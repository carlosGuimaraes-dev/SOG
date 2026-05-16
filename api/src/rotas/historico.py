"""
Rotas de histórico de processos emitidos/rejeitados.
"""
import csv
import io

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from typing import List

from auth import get_current_user
from sog_shared import db
from limiter import limiter
from schemas import HistoricoItemResponse

router = APIRouter(prefix="/historico", tags=["historico"])

CSV_FIELDNAMES = [
    "Número do processo",
    "Polo Ativo",
    "Valor Total",
    "Status",
    "Data de atualização",
    "Observação do operador",
]


def _fetch_historico_rows(conn, limit: int | None = None, offset: int | None = None):
    """Retorna todas as linhas do histórico, opcionalmente paginadas."""
    sql = """SELECT p.numero, d.polo_ativo, d.valor_total_recolher,
                    p.status, p.atualizado_em, d.obs_operador
             FROM processos p
             LEFT JOIN dados_processo d ON d.processo_id = p.id
             WHERE p.status IN ('emitido', 'rejeitado')
             ORDER BY p.atualizado_em DESC"""
    params = ()
    if limit is not None and offset is not None:
        sql += " LIMIT ? OFFSET ?"
        params = (limit, offset)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@router.get("", response_model=List[HistoricoItemResponse])
@limiter.limit("30/minute")
def historico(
    request: Request,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        rows = _fetch_historico_rows(conn, limit=limit, offset=offset)
        return rows


@router.get("/exportar")
@limiter.limit("10/minute")
def exportar_historico(
    request: Request,
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        rows = _fetch_historico_rows(conn)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "Número do processo": row.get("numero", ""),
            "Polo Ativo": row.get("polo_ativo", ""),
            "Valor Total": row.get("valor_total_recolher", ""),
            "Status": row.get("status", ""),
            "Data de atualização": row.get("atualizado_em", ""),
            "Observação do operador": row.get("obs_operador", ""),
        })

    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="historico.csv"'},
    )
