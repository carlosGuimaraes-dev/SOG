"""
Rotas de gerenciamento de tarefas assíncronas do agente.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from auth import get_current_user
from limiter import limiter
from sog_shared import db
from schemas import TarefaResponse, TarefaListResponse, CriarTarefaRequest

router = APIRouter(prefix="/tarefas", tags=["tarefas"])

SISTEMA_POR_TIPO = {
    "consultar_etiqueta_pje": "pje",
    "consultar_documentos_pje": "pje",
    "baixar_pdf_pje": "pje",
    "verificar_sessao_pje": "pje",
    "reautenticar_pje": "pje",
    "preencher_sistj": "sistj",
    "gravar_aprovar_sistj": "sistj",
    "verificar_sessao_sistj": "sistj",
    "reautenticar_sistj": "sistj",
    "anexar_demonstrativo_pje": "ambos",
    "reprocessar_processo": "ambos",
}

TIPOS_VALIDOS = set(SISTEMA_POR_TIPO.keys())


@router.post("", response_model=TarefaResponse)
@limiter.limit("20/minute")
def criar_tarefa(
    request: Request,
    req: CriarTarefaRequest,
    user: str = Depends(get_current_user),
):
    if req.tipo not in TIPOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Válidos: {', '.join(TIPOS_VALIDOS)}",
        )

    task_id = db.criar_tarefa(
        tipo=req.tipo,
        payload=req.payload,
        sistema_alvo=SISTEMA_POR_TIPO[req.tipo],
        criado_por=user,
    )
    tarefa = db.obter_tarefa(task_id)
    return tarefa


@router.get("", response_model=TarefaListResponse)
@limiter.limit("30/minute")
def listar_tarefas(
    request: Request,
    status: str = Query(None),
    tipo: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
):
    total, items = db.listar_tarefas(status=status, tipo=tipo, limit=limit, offset=offset)
    return {"total": total, "items": items}


@router.get("/{task_id}", response_model=TarefaResponse)
@limiter.limit("60/minute")
def obter_tarefa(
    task_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    tarefa = db.obter_tarefa(task_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa


@router.post("/{task_id}/cancelar", response_model=TarefaResponse)
@limiter.limit("10/minute")
def cancelar_tarefa(
    task_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    tarefa = db.obter_tarefa(task_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if tarefa.get("criado_por") != user:
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta tarefa")

    cancelado = db.cancelar_tarefa(task_id)
    if not cancelado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tarefa não pode ser cancelada (já em execução ou concluída)",
        )

    return db.obter_tarefa(task_id)
