import os
import sys
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Adiciona api/src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Adiciona shared/ ao path para importar sog_shared sem instalação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

# Variáveis obrigatórias para os testes
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-com-mais-de-32-caracteres!")

# Gera um hash bcrypt válido para testes que exercitam autenticação.
_test_hash = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode()
os.environ.setdefault("DASHBOARD_SENHA_HASH", _test_hash)

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
    from app import app

    with TestClient(app) as c:
        c.cookies.clear()
        yield c


@pytest.fixture
def auth_headers(mock_db):
    from auth import create_access_token

    token = create_access_token({"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}
