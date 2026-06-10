"""
Rotas de tarefas e status do PJe.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth import get_current_user
from limiter import limiter
from schemas import BaixarPdfRequest, SessaoStatusResponse, TarefaResponse
from sog_shared import db

router = APIRouter(prefix="/pje", tags=["pje"])

_RE_CNJ = re.compile(r"^\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}$")
_ESTADO_PENDING = "pending"
_ESTADO_ACTIVE = "active"
_ESTADO_EXPIRED = "expired"
_ESTADO_UNAVAILABLE = "unavailable"


def _mensagem_sessao(logado: bool, *, erro: bool = False) -> str:
    if erro:
        return "Falha na validação"
    if logado:
        return "Sessão ativa"
    return "Aguardando login"


def _sincronizar_tarefas_stale() -> None:
    db.reenfileirar_tarefas_stale(max_age_minutes=5)


def _criar_tarefa(tipo: str, payload: dict, user: str) -> dict:
    task_id = db.criar_tarefa(
        tipo=tipo,
        payload=payload,
        sistema_alvo="pje",
        criado_por=user,
    )
    return db.obter_tarefa(task_id)


def _status_sessao(tipo: str, sistema: str) -> dict:
    _sincronizar_tarefas_stale()
    _, items = db.listar_tarefas(tipo=tipo, limit=1, offset=0)
    if not items:
        return {
            "sistema": sistema,
            "estado": _ESTADO_PENDING,
            "logado": False,
            "mensagem": _mensagem_sessao(False),
            "ultima_verificacao": None,
        }

    tarefa = items[0]
    resultado = tarefa.get("resultado") or {}
    if tarefa["status"] == "concluido":
        logado = bool(resultado.get("logado"))
        return {
            "sistema": sistema,
            "estado": _ESTADO_ACTIVE if logado else _ESTADO_EXPIRED,
            "logado": logado,
            "mensagem": _mensagem_sessao(logado),
            "ultima_verificacao": tarefa.get("concluido_em") or tarefa.get("atualizado_em"),
        }

    if tarefa["status"] == "erro":
        return {
            "sistema": sistema,
            "estado": _ESTADO_UNAVAILABLE,
            "logado": False,
            "mensagem": _mensagem_sessao(False, erro=True),
            "ultima_verificacao": tarefa.get("concluido_em") or tarefa.get("atualizado_em"),
        }

    return {
        "sistema": sistema,
        "estado": _ESTADO_PENDING,
        "logado": False,
        "mensagem": _mensagem_sessao(False),
        "ultima_verificacao": tarefa.get("iniciado_em") or tarefa.get("atualizado_em"),
    }


@router.post("/consultar-etiqueta", response_model=TarefaResponse)
@limiter.limit("5/minute")
def consultar_etiqueta(request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa("consultar_etiqueta_pje", {}, user)


@router.post("/processos/{numero}/documentos", response_model=TarefaResponse)
@limiter.limit("10/minute")
def consultar_documentos(numero: str, request: Request, user: str = Depends(get_current_user)):
    if not _RE_CNJ.match(numero):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Número de processo inválido (CNJ)")
    return _criar_tarefa("consultar_documentos_pje", {"numero_processo": numero}, user)


@router.post("/documentos/{doc_id}/pdf", response_model=TarefaResponse)
@limiter.limit("10/minute")
def baixar_pdf(
    doc_id: str,
    req: BaixarPdfRequest,
    request: Request,
    user: str = Depends(get_current_user),
):
    if not doc_id.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doc_id inválido")
    return _criar_tarefa(
        "baixar_pdf_pje",
        {"numero_processo": req.numero_processo, "doc_id": doc_id},
        user,
    )


@router.get("/sessao", response_model=SessaoStatusResponse)
@limiter.limit("10/minute")
def sessao_pje(request: Request, user: str = Depends(get_current_user)):
    return _status_sessao("verificar_sessao_pje", "pje")


@router.post("/reautenticar", response_model=TarefaResponse)
@limiter.limit("2/minute")
def reautenticar_pje(request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa("reautenticar_pje", {}, user)
