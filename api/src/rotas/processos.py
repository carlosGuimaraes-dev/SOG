"""
Rotas de processos — listagem e detalhes.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import FileResponse

from auth import get_current_user
from sog_shared import db
from limiter import limiter
from schemas import ProcessoListResponse, ProcessoDetalheResponse, ProcessoResponse

SCREENSHOTS_BASE_DIR = Path("/dados/screenshots")

router = APIRouter(prefix="/processos", tags=["processos"])


@router.get("", response_model=ProcessoListResponse)
@limiter.limit("30/minute")
def listar_processos(
    request: Request,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
):
    pendentes = db.listar_aguardando_aprovacao(limit=limit, offset=offset)
    manuais = []
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'pendente_manual' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        manuais = [dict(r) for r in rows]
    return {"aguardando_aprovacao": pendentes, "pendente_manual": manuais}


@router.get("/{processo_id}", response_model=ProcessoDetalheResponse)
def detalhar_processo(
    processo_id: int,
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        processo = dict(row)

        # JOIN único para dados + documentos + logs em uma única conexão
        dados_row = conn.execute(
            "SELECT * FROM dados_processo WHERE processo_id = ? ORDER BY id DESC LIMIT 1",
            (processo_id,),
        ).fetchone()
        dados = dict(dados_row) if dados_row else None

        if dados:
            import json
            for campo in ("sucumbentes", "outros_itens", "compensacao", "custas_pagas"):
                if dados.get(campo):
                    try:
                        dados[campo] = json.loads(dados[campo])
                    except json.JSONDecodeError:
                        pass

        log_rows = conn.execute(
            "SELECT * FROM log_execucao WHERE processo_id = ? ORDER BY criado_em DESC",
            (processo_id,),
        ).fetchall()
        logs = [dict(r) for r in log_rows]

        doc_rows = conn.execute(
            "SELECT * FROM documentos_pje WHERE processo_id = ?",
            (processo_id,),
        ).fetchall()
        docs = [dict(r) for r in doc_rows]

    return {
        "processo": processo,
        "dados": dados,
        "logs": logs,
        "documentos": docs,
    }


@router.get("/{processo_id}/screenshot")
def screenshot(processo_id: int, user: str = Depends(get_current_user)):
    if processo_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de processo inválido",
        )

    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT numero FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        numero_processo = row["numero"]

    screenshots_dir = SCREENSHOTS_BASE_DIR.resolve()
    filename = f"{numero_processo}_sistjweb.png"
    file_path = (screenshots_dir / filename).resolve()

    # Proteção contra path traversal
    try:
        file_path.relative_to(screenshots_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caminho inválido",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot não encontrado",
        )

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )
