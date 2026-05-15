"""
Testes da API FastAPI.
"""
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app import app
from auth import create_access_token, create_refresh_token

client = TestClient(app)


class TestHealth:
    def test_health_publico(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("ok", "degraded")
        assert "version" in resp.json()
        assert "database" in resp.json()


class TestAuth:
    def test_login_credenciais_invalidas(self):
        resp = client.post("/auth/login", json={"username": "x", "password": "y"})
        assert resp.status_code == 401

    @patch("rotas.auth.authenticate_user", return_value=True)
    def test_login_sucesso(self, mock_auth):
        resp = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalido(self):
        resp = client.post("/auth/refresh", json={"refresh_token": "invalido"})
        assert resp.status_code == 401

    def test_refresh_token_sucesso(self):
        token = create_refresh_token({"sub": "admin"})
        resp = client.post("/auth/refresh", json={"refresh_token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data


class TestProtegido:
    def test_acesso_sem_token(self):
        resp = client.get("/processos")
        assert resp.status_code == 401

    def test_acesso_com_token_invalido(self):
        resp = client.get("/processos", headers={"Authorization": "Bearer xyz"})
        assert resp.status_code == 401

    def test_listar_processos_vazio(self):
        token = create_access_token({"sub": "admin"})
        resp = client.get("/processos", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "aguardando_aprovacao" in data
        assert "pendente_manual" in data


class TestAprovacao:
    def test_aprovar_processo_inexistente(self):
        token = create_access_token({"sub": "admin"})
        resp = client.post(
            "/aprovar/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_rejeitar_processo_inexistente(self):
        token = create_access_token({"sub": "admin"})
        resp = client.post(
            "/rejeitar/99999",
            json={"observacao": "teste"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestHistorico:
    def test_historico_paginado(self):
        token = create_access_token({"sub": "admin"})
        resp = client.get(
            "/historico?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
