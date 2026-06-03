import sqlite3

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
