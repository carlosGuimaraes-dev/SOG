"""
Testes dos endpoints de tarefas assíncronas.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

SCHEMA_SQL = Path(__file__).parent.parent.parent / "agente" / "src" / "banco" / "schema.sql"


@pytest.fixture
def mock_db(monkeypatch):
    """Fixture que substitui o banco SQLite por :memory: com schema inicializado."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    conn.commit()

    @contextmanager
    def _get_conn():
        yield conn

    monkeypatch.setattr("sog_shared.db.get_conn", _get_conn)
    monkeypatch.setattr("sog_shared.db.init_db", lambda: None)
    monkeypatch.setattr("sog_shared.config.init_config", lambda: None)

    yield conn

    conn.close()


@pytest.fixture
def client(mock_db):
    """Cliente de teste isolado."""
    from app import app

    with TestClient(app) as c:
        c.cookies.clear()
        yield c


@pytest.fixture
def auth_headers(mock_db):
    """Retorna headers com access token válido."""
    from auth import create_access_token

    token = create_access_token({"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}


class TestCriarTarefa:
    def test_criar_tarefa_sucesso(self, client, auth_headers):
        resp = client.post(
            "/api/v1/tarefas",
            json={"tipo": "verificar_sessao_pje", "payload": {}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["tipo"] == "verificar_sessao_pje"
        assert data["status"] == "pendente"
        assert data["payload"] == {}
        assert data["sistema_alvo"] == "pje"
        assert data["criado_por"] == "admin"

    def test_criar_tarefa_tipo_invalido(self, client, auth_headers):
        resp = client.post(
            "/api/v1/tarefas",
            json={"tipo": "tipo_inexistente", "payload": {}},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Tipo inválido" in resp.json()["detail"]

    def test_criar_tarefa_payload_customizado(self, client, auth_headers):
        resp = client.post(
            "/api/v1/tarefas",
            json={"tipo": "consultar_documentos_pje", "payload": {"numero_processo": "0000001-01.2024.8.07.0001"}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tipo"] == "consultar_documentos_pje"
        assert data["payload"]["numero_processo"] == "0000001-01.2024.8.07.0001"


class TestListarTarefas:
    def test_listar_vazio(self, client, auth_headers):
        resp = client.get("/api/v1/tarefas", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_listar_com_tarefas(self, client, auth_headers):
        # Cria duas tarefas
        client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_sistj"}, headers=auth_headers)

        resp = client.get("/api/v1/tarefas", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_listar_com_filtro_status(self, client, auth_headers):
        client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)

        resp = client.get("/api/v1/tarefas?status=pendente", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

        resp = client.get("/api/v1/tarefas?status=executando", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_listar_com_filtro_tipo(self, client, auth_headers):
        client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_sistj"}, headers=auth_headers)

        resp = client.get("/api/v1/tarefas?tipo=verificar_sessao_pje", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["tipo"] == "verificar_sessao_pje"

    def test_listar_paginacao(self, client, auth_headers):
        for _ in range(5):
            client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)

        resp = client.get("/api/v1/tarefas?limit=2&offset=0", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestObterTarefa:
    def test_obter_tarefa_existente(self, client, auth_headers):
        create_resp = client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/tarefas/{task_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == task_id
        assert data["tipo"] == "verificar_sessao_pje"

    def test_obter_tarefa_inexistente(self, client, auth_headers):
        resp = client.get("/api/v1/tarefas/9999", headers=auth_headers)
        assert resp.status_code == 404


class TestCancelarTarefa:
    def test_cancelar_tarefa_pendente(self, client, auth_headers):
        create_resp = client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.post(f"/api/v1/tarefas/{task_id}/cancelar", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelado"

    def test_cancelar_tarefa_nao_autorizado(self, client, auth_headers):
        # Cria tarefa como admin
        create_resp = client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        # Gera token para outro usuário
        from auth import create_access_token

        token = create_access_token({"sub": "outro_usuario"})
        outros_headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(f"/api/v1/tarefas/{task_id}/cancelar", headers=outros_headers)
        assert resp.status_code == 403

    def test_cancelar_tarefa_ja_executando(self, client, auth_headers, mock_db):
        create_resp = client.post("/api/v1/tarefas", json={"tipo": "verificar_sessao_pje"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        # Simula que a tarefa já está em execução
        mock_db.execute(
            "UPDATE agente_tarefas SET status = 'executando' WHERE id = ?",
            (task_id,),
        )
        mock_db.commit()

        resp = client.post(f"/api/v1/tarefas/{task_id}/cancelar", headers=auth_headers)
        assert resp.status_code == 400
        assert "não pode ser cancelada" in resp.json()["detail"]

    def test_cancelar_tarefa_inexistente(self, client, auth_headers):
        resp = client.post("/api/v1/tarefas/9999/cancelar", headers=auth_headers)
        assert resp.status_code == 404
