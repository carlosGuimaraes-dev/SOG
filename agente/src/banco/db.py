"""
Módulo de acesso ao banco SQLite.
"""
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _init_db():
    """Inicializa o banco com o schema se ainda não existir."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Processos ------------------------------------------------------------------

def processo_existe(numero: str) -> Optional[int]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM processos WHERE numero = ?", (numero,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "status": row["status"]}


def inserir_processo(numero: str, numero_sem_mascara: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO processos (numero, numero_sem_mascara) VALUES (?, ?)",
            (numero, numero_sem_mascara),
        )
        conn.commit()
        return cur.lastrowid


def atualizar_status(
    processo_id: int,
    status: str,
    erro_msg: Optional[str] = None,
    incrementar_tentativa: bool = False,
):
    with get_conn() as conn:
        if incrementar_tentativa:
            conn.execute(
                "UPDATE processos SET status = ?, erro_msg = ?, tentativas = tentativas + 1, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (status, erro_msg, processo_id),
            )
        else:
            conn.execute(
                "UPDATE processos SET status = ?, erro_msg = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (status, erro_msg, processo_id),
            )
        conn.commit()


def listar_pendentes() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status IN ('pendente', 'erro') AND tentativas < 3 ORDER BY criado_em"
        ).fetchall()
        return [dict(r) for r in rows]


def listar_aguardando_aprovacao() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aguardando_aprovacao' ORDER BY atualizado_em DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# Dados processo -------------------------------------------------------------

def salvar_dados_processo(processo_id: int, dados: Dict[str, Any]) -> int:
    campos = list(dados.keys())
    valores = list(dados.values())
    # Converte listas/dicts para JSON strings
    for i, v in enumerate(valores):
        if isinstance(v, (list, dict)):
            valores[i] = json.dumps(v, ensure_ascii=False)

    placeholders = ", ".join(["?"] * len(campos))
    colunas = ", ".join(campos)

    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO dados_processo (processo_id, {colunas}) VALUES (?, {placeholders})",
            (processo_id, *valores),
        )
        conn.commit()
        return cur.lastrowid


def obter_dados_processo(processo_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM dados_processo WHERE processo_id = ? ORDER BY id DESC LIMIT 1",
            (processo_id,),
        ).fetchone()
        if not row:
            return None
        dados = dict(row)
        # Deserializa JSON
        for campo in ("sucumbentes", "outros_itens", "compensacao", "custas_pagas"):
            if dados.get(campo):
                try:
                    dados[campo] = json.loads(dados[campo])
                except json.JSONDecodeError:
                    pass
        return dados


# Documentos PJE -------------------------------------------------------------

def salvar_documento(
    processo_id: int, doc_id: str, tipo: str, data_assinatura: str, nome: str
):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO documentos_pje (processo_id, doc_id, tipo, data_assinatura, nome) VALUES (?, ?, ?, ?, ?)",
            (processo_id, doc_id, tipo, data_assinatura, nome),
        )
        conn.commit()


def listar_documentos(processo_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos_pje WHERE processo_id = ?", (processo_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# Log ------------------------------------------------------------------------

def registrar_log(processo_id: Optional[int], etapa: str, status: str, mensagem: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO log_execucao (processo_id, etapa, status, mensagem) VALUES (?, ?, ?, ?)",
            (processo_id, etapa, status, mensagem),
        )
        conn.commit()


def listar_logs(processo_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM log_execucao WHERE processo_id = ? ORDER BY criado_em DESC",
            (processo_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# Inicialização --------------------------------------------------------------
_init_db()
