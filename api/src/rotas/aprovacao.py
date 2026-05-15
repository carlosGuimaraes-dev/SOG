"""
Rotas de aprovação e rejeição de processos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "agente" / "src"))

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import threading

from auth import get_current_user
from banco import db
from modulos.emissor import emitir_e_anexar

router = APIRouter(tags=["aprovacao"])


class RejeicaoRequest(BaseModel):
    observacao: str = ""


@router.post("/aprovar/{processo_id}")
def aprovar_processo(processo_id: int, user: str = Depends(get_current_user)):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        if row["status"] != "aguardando_aprovacao":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processo não está aguardando aprovação",
            )

    db.atualizar_status(processo_id, "aprovado")
    db.registrar_log(processo_id, "aprovacao", "ok", f"Aprovado por {user}")

    # Dispara emissão em background
    threading.Thread(target=emitir_e_anexar, args=(processo_id,), daemon=True).start()

    return {"message": "Aprovação registrada. Emissão em andamento."}


@router.post("/rejeitar/{processo_id}")
def rejeitar_processo(
    processo_id: int, req: RejeicaoRequest, user: str = Depends(get_current_user)
):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

    db.atualizar_status(processo_id, "rejeitado")
    db.registrar_log(
        processo_id, "rejeicao", "ok", f"Rejeitado por {user}: {req.observacao}"
    )

    with db.get_conn() as conn:
        conn.execute(
            "UPDATE dados_processo SET obs_operador = ? WHERE processo_id = ?",
            (req.observacao, processo_id),
        )
        conn.commit()

    return {"message": "Processo rejeitado."}
