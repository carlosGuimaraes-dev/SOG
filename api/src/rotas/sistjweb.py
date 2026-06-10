"""
Rotas de tarefas e status do SISTJWEB.
"""
from fastapi import APIRouter, Depends, Request

from auth import get_current_user
from limiter import limiter
from schemas import SessaoStatusResponse, TarefaResponse
from sog_shared import db

router = APIRouter(prefix="/sistj", tags=["sistj"])
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
        sistema_alvo="sistj",
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


@router.post("/preencher/{processo_id}", response_model=TarefaResponse)
@limiter.limit("10/minute")
def preencher_sistj(processo_id: int, request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa("preencher_sistj", {"processo_id": processo_id}, user)


@router.post("/gravar-aprovar/{processo_id}", response_model=TarefaResponse)
@limiter.limit("10/minute")
def gravar_aprovar_sistj(
    processo_id: int,
    request: Request,
    user: str = Depends(get_current_user),
):
    return _criar_tarefa("gravar_aprovar_sistj", {"processo_id": processo_id}, user)


@router.get("/sessao", response_model=SessaoStatusResponse)
@limiter.limit("10/minute")
def sessao_sistj(request: Request, user: str = Depends(get_current_user)):
    return _status_sessao("verificar_sessao_sistj", "sistj")


@router.post("/reautenticar", response_model=TarefaResponse)
@limiter.limit("2/minute")
def reautenticar_sistj(request: Request, user: str = Depends(get_current_user)):
    return _criar_tarefa("reautenticar_sistj", {}, user)
