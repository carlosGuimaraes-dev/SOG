"""
Módulo de acesso ao banco SQLite — versão compartilhada.

Sem side-effects no import. init_db() deve ser chamada explicitamente.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# DB_PATH pode vir de variável de ambiente ou do pacote shared config
from sog_shared.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

COLUNAS_PERMITIDAS_DADOS_PROCESSO = frozenset({
    "instancia",
    "processo_eletronico",
    "circunscricao",
    "competencia",
    "feito",
    "classe",
    "valor_causa",
    "valor_causa_atualizado",
    "data_distribuicao",
    "polo_ativo",
    "polo_passivo",
    "tipo_guia",
    "pro_rata",
    "sucumbentes",
    "ids_oficios",
    "ids_alvaras",
    "ids_traslados",
    "ids_mandados",
    "ids_cartas_sentenca",
    "ids_ar",
    "ids_armp",
    "ids_circunscricao_origem",
    "ids_outra_circunscricao",
    "outros_itens",
    "compensacao",
    "custas_pagas",
    "sucumbente_nome",
    "sucumbente_cpf_cnpj",
    "sucumbente_tipo",
    "honorarios_percentual",
    "suspensao_exigibilidade",
    "valor_total_recolher",
    "area_direito",
    "obs_operador",
    "screenshot_path",
})


def _setup_conn(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Aplica PRAGMAs de concorrência e configura row_factory."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    """Inicializa o banco com o schema se ainda não existir.

    Deve ser chamada explicitamente no startup da aplicação.
    """
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        _setup_conn(conn)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    _setup_conn(conn)
    try:
        yield conn
    finally:
        conn.close()


# Processos ------------------------------------------------------------------

def processo_existe(numero: str) -> Optional[Dict[str, Any]]:
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


def listar_pendentes(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status IN ('pendente', 'erro') AND tentativas < 3 ORDER BY criado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def listar_aguardando_aprovacao(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aguardando_aprovacao' ORDER BY atualizado_em DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# Dados processo -------------------------------------------------------------

def salvar_dados_processo(processo_id: int, dados: Dict[str, Any]) -> int:
    campos = list(dados.keys())
    invalidas = set(campos) - COLUNAS_PERMITIDAS_DADOS_PROCESSO
    if invalidas:
        raise ValueError(
            f"Colunas não permitidas em dados_processo: {sorted(invalidas)}"
        )

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


# Agente controle ------------------------------------------------------------

def obter_controle_agente() -> Optional[Dict[str, Any]]:
    """Retorna o registro de controle do agente (id=1) ou None."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM agente_controle WHERE id = 1").fetchone()
        return dict(row) if row else None


def criar_ou_atualizar_controle_agente(
    comando: Optional[str] = None,
    status: Optional[str] = None,
    mensagem: Optional[str] = None,
    pid: Optional[int] = None,
) -> None:
    """
    Upsert na tabela agente_controle (id=1).
    Campos None são ignorados (mantêm valor atual).
    Usa BEGIN IMMEDIATE para evitar race condition entre API e agente.
    """
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT id FROM agente_controle WHERE id = 1").fetchone()
            if row:
                campos = []
                vals = []
                if comando is not None:
                    campos.append("comando = ?")
                    vals.append(comando)
                if status is not None:
                    campos.append("status = ?")
                    vals.append(status)
                if mensagem is not None:
                    campos.append("mensagem = ?")
                    vals.append(mensagem)
                if pid is not None:
                    campos.append("pid = ?")
                    vals.append(pid)
                if campos:
                    campos.append("atualizado_em = CURRENT_TIMESTAMP")
                    conn.execute(
                        f"UPDATE agente_controle SET {', '.join(campos)} WHERE id = 1",
                        vals,
                    )
                    conn.commit()
            else:
                conn.execute(
                    "INSERT INTO agente_controle (id, comando, status, mensagem, pid) VALUES (1, ?, ?, ?, ?)",
                    (comando or 'parar', status or 'parado', mensagem or '', pid),
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise


def listar_aprovados(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE status = 'aprovado' ORDER BY atualizado_em LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# Tarefas -------------------------------------------------------------------

def criar_tarefa(tipo: str, payload: Dict[str, Any], sistema_alvo: str, criado_por: str) -> int:
    """Insere nova tarefa e retorna o id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO agente_tarefas (tipo, payload, sistema_alvo, criado_por) VALUES (?, ?, ?, ?)",
            (tipo, json.dumps(payload), sistema_alvo, criado_por),
        )
        conn.commit()
        return cur.lastrowid


def obter_tarefa(task_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        tarefa = dict(row)
        for campo in ("payload", "resultado"):
            if tarefa.get(campo):
                try:
                    tarefa[campo] = json.loads(tarefa[campo])
                except json.JSONDecodeError:
                    pass
        return tarefa


def listar_tarefas(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    with get_conn() as conn:
        where = ["1=1"]
        params: List[Any] = []
        if status:
            where.append("status = ?")
            params.append(status)
        if tipo:
            where.append("tipo = ?")
            params.append(tipo)

        where_sql = " AND ".join(where)

        total_row = conn.execute(
            f"SELECT COUNT(*) FROM agente_tarefas WHERE {where_sql}", params
        ).fetchone()
        total = total_row[0] if total_row else 0

        rows = conn.execute(
            f"SELECT * FROM agente_tarefas WHERE {where_sql} ORDER BY criado_em DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            for campo in ("payload", "resultado"):
                if item.get(campo):
                    try:
                        item[campo] = json.loads(item[campo])
                    except json.JSONDecodeError:
                        pass
            items.append(item)
        return total, items


def proxima_tarefa_pendente() -> Optional[Dict[str, Any]]:
    """
    Pega a próxima tarefa pendente (atomicamente) e marca como executando.
    Retorna None se não houver.
    """
    with get_conn() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM agente_tarefas WHERE status = 'pendente' ORDER BY criado_em LIMIT 1"
            ).fetchone()
            if not row:
                conn.rollback()
                return None

            task_id = row["id"]
            conn.execute(
                "UPDATE agente_tarefas SET status = 'executando', iniciado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,),
            )
            conn.commit()

            tarefa = dict(row)
            tarefa["status"] = "executando"
            if tarefa.get("payload"):
                try:
                    tarefa["payload"] = json.loads(tarefa["payload"])
                except json.JSONDecodeError:
                    pass
            return tarefa
        except Exception:
            conn.rollback()
            raise


def concluir_tarefa(
    task_id: int,
    status: str,
    resultado: Optional[Dict[str, Any]] = None,
    mensagem_erro: Optional[str] = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE agente_tarefas
               SET status = ?, resultado = ?, mensagem_erro = ?, concluido_em = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, json.dumps(resultado) if resultado else "{}", mensagem_erro or "", task_id),
        )
        conn.commit()


def cancelar_tarefa(task_id: int) -> bool:
    """Cancela uma tarefa se ainda estiver pendente. Retorna True se cancelou."""
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status FROM agente_tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if not row or row["status"] != "pendente":
            conn.rollback()
            return False
        conn.execute(
            "UPDATE agente_tarefas SET status = 'cancelado', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        return True


def contar_tarefas_por_status() -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM agente_tarefas GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}
