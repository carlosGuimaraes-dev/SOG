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
router = APIRouter(tags=["aprovacao"])


class RejeicaoRequest(BaseModel):
    observacao: str = ""


def _disparar_emissao(processo_id: int) -> None:
    """Tenta disparar emissão em background; falha silenciosamente se agente não disponível."""
    try:
        from modulos.emissor import emitir_e_anexar
        threading.Thread(target=emitir_e_anexar, args=(processo_id,), daemon=True).start()
    except Exception as exc:
        import logging
        logging.getLogger("custas_api").warning(
            "Emissor não disponível no container API (falta Playwright). "
            "Processo %d marcado como aprovado; execute o agente para emissão. Erro: %s",
            processo_id, exc,
        )


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

    _disparar_emissao(processo_id)

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
