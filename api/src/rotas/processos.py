"""
Rotas de processos — listagem e detalhes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "agente" / "src"))

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from auth import get_current_user
from banco import db

router = APIRouter(prefix="/processos", tags=["processos"])


@router.get("", response_model=Dict[str, List[Dict[str, Any]]])
def listar_processos(user: str = Depends(get_current_user)):
    pendentes = db.listar_aguardando_aprovacao()
    manuais = []
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'pendente_manual' ORDER BY atualizado_em DESC"
        ).fetchall()
        manuais = [dict(r) for r in rows]
    return {"aguardando_aprovacao": pendentes, "pendente_manual": manuais}


@router.get("/{processo_id}")
def detalhar_processo(processo_id: int, user: str = Depends(get_current_user)):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        processo = dict(row)
        dados = db.obter_dados_processo(processo_id)
        logs = db.listar_logs(processo_id)
        docs = db.listar_documentos(processo_id)

    return {
        "processo": processo,
        "dados": dados,
        "logs": logs,
        "documentos": docs,
    }
