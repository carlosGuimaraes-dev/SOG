"""
Rotas de aprovação e rejeição de processos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request

from auth import get_current_user
from sog_shared import db
from limiter import limiter
from schemas import AprovacaoResponse, RejeicaoResponse, RejeicaoRequest

router = APIRouter(tags=["aprovacao"])


def _disparar_emissao(processo_id: int) -> None:
    """Tenta disparar emissão em background; falha silenciosamente se agente não disponível."""
    try:
        from modulos.emissor import emitir_e_anexar
        emitir_e_anexar(processo_id)
    except Exception as exc:
        import logging
        logging.getLogger("custas_api").warning(
            "Emissor não disponível no container API (falta Playwright). "
            "Processo %d marcado como aprovado; execute o agente para emissão. Erro: %s",
            processo_id, exc,
        )


@router.post("/aprovar/{processo_id}", response_model=AprovacaoResponse)
@limiter.limit("10/minute")
def aprovar_processo(
    processo_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    user: str = Depends(get_current_user),
):
    with db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        if row["status"] != "aguardando_aprovacao":
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processo não está aguardando aprovação",
            )

        conn.execute(
            "UPDATE processos SET status = 'aprovado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (processo_id,),
        )
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, "aprovacao", "ok", f"Aprovado por {user}"),
        )
        conn.commit()

    background_tasks.add_task(_disparar_emissao, processo_id)

    return {"message": "Aprovação registrada. Emissão em andamento."}


@router.post("/rejeitar/{processo_id}", response_model=RejeicaoResponse)
def rejeitar_processo(
    processo_id: int,
    req: RejeicaoRequest,
    user: str = Depends(get_current_user),
):
    observacao_segura = req.observacao.replace("\n", " ").replace("\r", "")[:500]

    with db.get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        conn.execute(
            "UPDATE processos SET status = 'rejeitado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (processo_id,),
        )
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, "rejeicao", "ok", f"Rejeitado por {user}: {observacao_segura}"),
        )
        conn.execute(
            "UPDATE dados_processo SET obs_operador = ? WHERE processo_id = ?",
            (req.observacao, processo_id),
        )
        conn.commit()

    return {"message": "Processo rejeitado."}
