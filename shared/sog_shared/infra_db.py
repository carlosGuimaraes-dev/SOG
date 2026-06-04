"""
Infraestrutura compartilhada de banco SQLite.

Este módulo concentra schema, conexão e evolução compatível do banco,
sem expor operações de domínio.
"""
from contextlib import contextmanager
from pathlib import Path
import sys
import sqlite3

from sog_shared.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_COLUNAS_OBRIGATORIAS_POR_TABELA = {
    "agente_controle": {
        "ciclo_uuid": "TEXT",
        "ciclo_snapshot": "TEXT DEFAULT '{}'",
        "pausado_em": "DATETIME",
        "retomado_em": "DATETIME",
    },
    "processos": {
        "reprocessar_solicitado_em": "DATETIME",
        "reprocessar_solicitado_por": "TEXT",
        "reprocessar_motivo": "TEXT",
    },
    "agente_ciclo_membros": {
        "processado_em": "DATETIME",
    },
    "log_execucao": {
        "chave_idempotencia": "TEXT",
    },
}


def _setup_conn(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _garantir_colunas_tabela(
    conn: sqlite3.Connection,
    tabela: str,
    colunas: dict[str, str],
) -> None:
    existentes = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    }
    for coluna, definicao in colunas.items():
        if coluna not in existentes:
            conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def _garantir_schema_runtime(conn: sqlite3.Connection) -> None:
    for tabela, colunas in _COLUNAS_OBRIGATORIAS_POR_TABELA.items():
        _garantir_colunas_tabela(conn, tabela, colunas)
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_log_execucao_chave
            ON log_execucao (COALESCE(processo_id, -1), etapa, status, chave_idempotencia)
            WHERE chave_idempotencia IS NOT NULL
        """
    )


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        _setup_conn(conn)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _garantir_schema_runtime(conn)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    db_module = sys.modules.get("sog_shared.db")
    db_get_conn = getattr(db_module, "get_conn", None) if db_module else None
    if db_get_conn is not None and db_get_conn is not get_conn:
        with db_get_conn() as conn:
            yield conn
        return

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    _setup_conn(conn)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    _garantir_schema_runtime(conn)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()
