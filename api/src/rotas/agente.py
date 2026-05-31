"""
Rotas de controle do agente de automação.
A API escreve comandos (iniciar/parar); o agente lê e executa.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from limiter import limiter
from schemas import AgenteStatusResponse, AgenteComandoResponse, CicloAgenteResponse
from sog_shared import db

router = APIRouter(prefix="/agente", tags=["agente"])


@router.post("/iniciar", response_model=AgenteComandoResponse)
@limiter.limit("10/minute")
def iniciar_agente(
    request: Request,
    user: str = Depends(get_current_user),
):
    resultado = db.solicitar_inicio_agente()
    if not resultado["accepted"]:
        raise HTTPException(
            status_code=409,
            detail="Já existe um ciclo do agente em execução.",
        )
    acao = "retomado" if resultado.get("resumed") else "iniciado"
    return {
        "message": f"Ciclo {acao}.",
        "ciclo_uuid": resultado.get("ciclo_uuid"),
        "resumed": resultado.get("resumed", False),
    }


@router.post("/parar", response_model=AgenteComandoResponse)
@limiter.limit("10/minute")
def parar_agente(
    request: Request,
    user: str = Depends(get_current_user),
):
    resultado = db.solicitar_parada_agente()
    if resultado.get("already_paused"):
        return {"message": "Ciclo já está pausado.", "ciclo_uuid": resultado.get("ciclo_uuid")}
    return {"message": "Parada cooperativa solicitada.", "ciclo_uuid": resultado.get("ciclo_uuid")}


@router.get("/status", response_model=AgenteStatusResponse)
@limiter.limit("10/minute")
def status_agente(
    request: Request,
    user: str = Depends(get_current_user),
):
    controle = db.obter_controle_agente()
    if not controle:
        return {
            "status": "desconhecido",
            "mensagem": "Agente não registrado. Execute o aplicativo no desktop.",
            "atualizado_em": None,
            "online": False,
        }

    online = False
    if controle.get("atualizado_em"):
        try:
            atualizado_str = controle["atualizado_em"]
            if isinstance(atualizado_str, str):
                if atualizado_str.endswith('Z'):
                    atualizado_str = atualizado_str[:-1] + '+00:00'
                try:
                    ultimo = datetime.fromisoformat(atualizado_str)
                except ValueError:
                    ultimo = datetime.strptime(atualizado_str, "%Y-%m-%d %H:%M:%S")
            else:
                ultimo = atualizado_str

            # SQLite retorna timestamps sem timezone — assumimos UTC
            if ultimo.tzinfo is None:
                ultimo = ultimo.replace(tzinfo=timezone.utc)

            agora = datetime.now(timezone.utc)
            diff = (agora - ultimo).total_seconds()
            online = diff < 90  # 90 segundos = tolerância para 1 ciclo + margem
        except Exception:
            pass

    return {
        "status": controle["status"],
        "mensagem": controle.get("mensagem", ""),
        "atualizado_em": controle.get("atualizado_em"),
        "online": online,
        "ciclo_uuid": controle.get("ciclo_uuid"),
        "ciclo_snapshot": controle.get("ciclo_snapshot"),
        "pausado_em": controle.get("pausado_em"),
        "retomado_em": controle.get("retomado_em"),
        "pode_iniciar": controle["status"] not in db.ESTADOS_CICLO_ATIVO,
        "pode_parar": controle["status"] in db.ESTADOS_CICLO_ATIVO,
        "relogin_required": controle["status"] == "aguardando_login",
    }


@router.get("/ciclos/atual", response_model=Optional[CicloAgenteResponse])
@limiter.limit("10/minute")
def ciclo_atual(
    request: Request,
    user: str = Depends(get_current_user),
):
    ciclo = db.obter_ciclo_atual()
    if not ciclo:
        return None
    return db.obter_ciclo_com_membros(ciclo["uuid"])


@router.get("/ciclos/ultimo", response_model=Optional[CicloAgenteResponse])
@limiter.limit("10/minute")
def ultimo_ciclo(
    request: Request,
    user: str = Depends(get_current_user),
):
    ciclo = db.obter_ultimo_ciclo()
    if not ciclo:
        return None
    return db.obter_ciclo_com_membros(ciclo["uuid"])


@router.get("/ciclos/{ciclo_uuid}", response_model=CicloAgenteResponse)
@limiter.limit("10/minute")
def detalhe_ciclo(
    ciclo_uuid: str,
    request: Request,
    user: str = Depends(get_current_user),
):
    ciclo = db.obter_ciclo_com_membros(ciclo_uuid)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado")
    return ciclo
