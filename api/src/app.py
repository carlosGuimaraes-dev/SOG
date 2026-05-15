"""
API FastAPI para dashboard de aprovação de custas TJDFT.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agente" / "src"))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from config import DASHBOARD_USUARIO, DASHBOARD_SENHA_HASH
from banco import db
from modulos.emissor import emitir_e_anexar

app = FastAPI(title="Custas TJDFT API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()


def verificar_auth(credentials: HTTPBasicCredentials = Depends(security)):
    # Em produção, usar hash bcrypt. Aqui simplificado para .env
    if credentials.username != DASHBOARD_USUARIO:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    # TODO: implementar verificação de hash bcrypt
    return credentials.username


class RejeicaoRequest(BaseModel):
    observacao: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/processos")
def listar_processos(user: str = Depends(verificar_auth)):
    pendentes = db.listar_aguardando_aprovacao()
    manuais = []
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'pendente_manual' ORDER BY atualizado_em DESC"
        ).fetchall()
        manuais = [dict(r) for r in rows]
    return {"aguardando_aprovacao": pendentes, "pendente_manual": manuais}


@app.get("/processos/{processo_id}")
def detalhar_processo(processo_id: int, user: str = Depends(verificar_auth)):
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


@app.post("/aprovar/{processo_id}")
def aprovar_processo(processo_id: int, user: str = Depends(verificar_auth)):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        if row["status"] != "aguardando_aprovacao":
            raise HTTPException(status_code=400, detail="Processo não está aguardando aprovação")

    db.atualizar_status(processo_id, "aprovado")
    db.registrar_log(processo_id, "aprovacao", "ok", f"Aprovado por {user}")

    # Dispara emissão em background (simplificado)
    import threading
    threading.Thread(target=emitir_e_anexar, args=(processo_id,), daemon=True).start()

    return {"message": "Aprovação registrada. Emissão em andamento."}


@app.post("/rejeitar/{processo_id}")
def rejeitar_processo(processo_id: int, req: RejeicaoRequest, user: str = Depends(verificar_auth)):
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM processos WHERE id = ?", (processo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

    db.atualizar_status(processo_id, "rejeitado")
    db.registrar_log(processo_id, "rejeicao", "ok", f"Rejeitado por {user}: {req.observacao}")

    with db.get_conn() as conn:
        conn.execute(
            "UPDATE dados_processo SET obs_operador = ? WHERE processo_id = ?",
            (req.observacao, processo_id),
        )
        conn.commit()

    return {"message": "Processo rejeitado."}


@app.get("/historico")
def historico(limit: int = 50, offset: int = 0, user: str = Depends(verificar_auth)):
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT p.*, d.polo_ativo, d.valor_total_recolher, d.obs_operador
               FROM processos p
               LEFT JOIN dados_processo d ON d.processo_id = p.id
               WHERE p.status IN ('emitido', 'rejeitado')
               ORDER BY p.atualizado_em DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
