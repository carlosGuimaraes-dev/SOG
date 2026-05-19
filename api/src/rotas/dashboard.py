"""
Resumo consolidado do estado do agente e das últimas verificações de sessão.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from auth import get_current_user
from limiter import limiter
from schemas import DashboardSessoesResponse
from sog_shared import db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _agente_online(controle: dict | None) -> bool:
    if not controle or not controle.get("atualizado_em"):
        return False

    atualizado = controle["atualizado_em"]
    try:
        if isinstance(atualizado, str):
            if atualizado.endswith("Z"):
                atualizado = atualizado[:-1] + "+00:00"
            ultimo = datetime.fromisoformat(atualizado)
        else:
            ultimo = atualizado
        if ultimo.tzinfo is None:
            ultimo = ultimo.replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - ultimo).total_seconds()
        return diff < 90
    except Exception:
        return False


def _status_sessao(tipo: str, sistema: str) -> dict:
    _, items = db.listar_tarefas(tipo=tipo, limit=1, offset=0)
    if not items:
        return {
            "sistema": sistema,
            "logado": False,
            "mensagem": "Desconhecido",
            "ultima_verificacao": None,
        }

    tarefa = items[0]
    resultado = tarefa.get("resultado") or {}
    if tarefa["status"] == "concluido":
        logado = bool(resultado.get("logado"))
        return {
            "sistema": sistema,
            "logado": logado,
            "mensagem": "Sessão ativa" if logado else "Sessão inativa",
            "ultima_verificacao": tarefa.get("concluido_em") or tarefa.get("atualizado_em"),
        }
    if tarefa["status"] == "erro":
        return {
            "sistema": sistema,
            "logado": False,
            "mensagem": tarefa.get("mensagem_erro") or "Falha na verificação",
            "ultima_verificacao": tarefa.get("concluido_em") or tarefa.get("atualizado_em"),
        }

    return {
        "sistema": sistema,
        "logado": False,
        "mensagem": f"Última verificação em {tarefa['status']}",
        "ultima_verificacao": tarefa.get("iniciado_em") or tarefa.get("atualizado_em"),
    }


@router.get("/sessoes", response_model=DashboardSessoesResponse)
@limiter.limit("30/minute")
def dashboard_sessoes(request: Request, user: str = Depends(get_current_user)):
    controle = db.obter_controle_agente() or {}
    status_counts = db.contar_tarefas_por_status()
    return {
        "pje": _status_sessao("verificar_sessao_pje", "pje"),
        "sistj": _status_sessao("verificar_sessao_sistj", "sistj"),
        "agente_online": _agente_online(controle),
        "agente_status": controle.get("status", "desconhecido"),
        "tarefas_pendentes": status_counts.get("pendente", 0),
        "tarefas_executando": status_counts.get("executando", 0),
    }
