"""
Configuração compartilhada entre API e Agente.

Variáveis de ambiente lidas no import (sem side-effects):
  - DB_PATH, TIMEOUT_PADRAO, HEADLESS, MAX_TENTATIVAS
  - DASHBOARD_USUARIO, DASHBOARD_SENHA

A função init_config() deve ser chamada explicitamente no startup
para criar diretórios necessários.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
_db_path_env = os.getenv("DB_PATH", "")
if _db_path_env:
    DB_PATH = _db_path_env
else:
    # Fallback para desenvolvimento local (fora do container)
    DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "dados" / "custas.db")

# ---------------------------------------------------------------------------
# Dashboard / Auth
# ---------------------------------------------------------------------------
DASHBOARD_USUARIO = os.getenv("DASHBOARD_USUARIO", "admin")
DASHBOARD_SENHA = os.getenv("DASHBOARD_SENHA", "")

# ---------------------------------------------------------------------------
# Playwright / Execução
# ---------------------------------------------------------------------------
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
MAX_TENTATIVAS = int(os.getenv("MAX_TENTATIVAS", "3"))
TIMEOUT_PADRAO = int(os.getenv("TIMEOUT_PADRAO", "30000"))


# ---------------------------------------------------------------------------
# Diretórios derivados
# ---------------------------------------------------------------------------
def _dados_dir() -> Path:
    return Path(DB_PATH).parent


def screenshots_dir() -> Path:
    return _dados_dir() / "screenshots"


def demonstrativos_dir() -> Path:
    return _dados_dir() / "demonstrativos"


# ---------------------------------------------------------------------------
# Inicialização explícita (chamar no startup)
# ---------------------------------------------------------------------------
def init_config() -> None:
    """Cria diretórios necessários. Seguro para chamar múltiplas vezes."""
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        screenshots_dir().mkdir(parents=True, exist_ok=True)
        demonstrativos_dir().mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
