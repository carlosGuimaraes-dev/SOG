"""
Rotas de ações pontuais em processos.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from limiter import limiter
from schemas import ReprocessamentoRequest, ReprocessamentoResponse, TarefaResponse
from sog_shared import db

router = APIRouter(prefix="/processos", tags=["acoes"])


def _criar_tarefa(tipo: str, payload: dict, user: str) -> dict:
    task_id = db.criar_tarefa(
        tipo=tipo,
        payload=payload,
        sistema_alvo="ambos",
        criado_por=user,
    )
    return db.obter_tarefa(task_id)


@router.post("/{processo_id}/reprocessar", response_model=ReprocessamentoResponse)
@limiter.limit("5/minute")
def reprocessar_processo(
    processo_id: int,
    req: ReprocessamentoRequest,
    request: Request,
    user: str = Depends(get_current_user),
):
    resultado = db.solicitar_reprocessamento(processo_id, user, req.motivo)
    if resultado["accepted"]:
        return {
            "message": "Reprocessamento solicitado para o próximo ciclo.",
            "processo": resultado["processo"],
        }
    if resultado["reason"] == "not_found":
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    raise HTTPException(
        status_code=409,
        detail="Reprocessamento permitido apenas para erro, pendente_manual e rejeitado.",
    )


@router.post("/{processo_id}/anexar-demonstrativo", response_model=TarefaResponse)
@limiter.limit("5/minute")
def anexar_demonstrativo(
    processo_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    return _criar_tarefa("anexar_demonstrativo_pje", {"processo_id": processo_id}, user)
