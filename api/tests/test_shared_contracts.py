import sqlite3

from sog_shared import db as shared_db
import schemas as api_schemas
from sog_shared import schemas as shared_schemas
from sog_shared.infra_db import SCHEMA_PATH
from sog_shared import runtime_preparation


def test_api_reusa_modelos_compartilhados():
    assert api_schemas.ProcessoResponse is shared_schemas.ProcessoResponse
    assert api_schemas.ProcessoDetalheResponse is shared_schemas.ProcessoDetalheResponse
    assert api_schemas.AgenteStatusResponse is shared_schemas.AgenteStatusResponse
    assert api_schemas.AgenteComandoResponse is shared_schemas.AgenteComandoResponse
    assert api_schemas.TarefaResponse is shared_schemas.TarefaResponse


def test_shared_nao_expoe_contratos_de_auth_do_dashboard():
    assert not hasattr(shared_schemas, "LoginResponse")
    assert not hasattr(shared_schemas, "TokenRefreshResponse")
    assert not hasattr(shared_schemas, "LogoutResponse")
    assert not hasattr(shared_schemas, "MeResponse")


def test_schema_compartilhado_inicializa_tabelas_canonicas():
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        tabelas = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "processos" in tabelas
    assert "dados_processo" in tabelas
    assert "agente_tarefas" in tabelas


def test_runtime_preparation_reusa_bootstrap_compartilhado(monkeypatch):
    chamadas = []

    monkeypatch.setattr(runtime_preparation, "init_config", lambda: chamadas.append("config"))
    monkeypatch.setattr(runtime_preparation, "init_db", lambda: chamadas.append("db"))

    runtime_preparation.prepare_runtime()

    assert chamadas == ["config", "db"]
    assert runtime_preparation.SCHEMA_PATH == SCHEMA_PATH


def test_facade_compartilhada_persiste_credenciais_dashboard_na_conexao_monkeypatched(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()

    class _ConnCtx:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(shared_db, "get_conn", lambda: _ConnCtx())

    shared_db.salvar_credenciais_dashboard("operador", "segredo")
    credenciais = shared_db.obter_credenciais_dashboard()

    assert credenciais == {"usuario": "operador", "senha": "segredo"}

    conn.close()
