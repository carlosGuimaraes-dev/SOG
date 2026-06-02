"""
Configuração do agente de custas processuais TJDFT.
Lê variáveis de ambiente do .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# PJE
PJE_URL = os.getenv("PJE_URL", "https://pje.tjdft.jus.br")
PJE_ETIQUETA = os.getenv("PJE_ETIQUETA", "SHEILA DE DEUS (TREINAMENTO)")

# SISTJWEB
SISTJ_URL = os.getenv("SISTJ_URL", "https://sistj.tjdft.jus.br/sistj/sistj")

# Datajud API
DATAJUD_API_KEY = os.getenv("DATAJUD_API_KEY", "")
DATAJUD_URL = os.getenv(
    "DATAJUD_URL",
    "https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search",
)

# Dashboard
DASHBOARD_USUARIO = os.getenv("DASHBOARD_USUARIO", "admin")
DASHBOARD_SENHA = os.getenv("DASHBOARD_SENHA", "")

# Notificação
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORTA = int(os.getenv("SMTP_PORTA", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_SENHA = os.getenv("SMTP_SENHA", "")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Caminhos
_db_path_env = os.getenv("DB_PATH", "")
if _db_path_env:
    DB_PATH = _db_path_env
else:
    DB_PATH = str(PROJECT_ROOT / "dados" / "custas.db")

DADOS_DIR = Path(DB_PATH).parent
SCREENSHOTS_DIR = DADOS_DIR / "screenshots"
DEMONSTRATIVOS_DIR = DADOS_DIR / "demonstrativos"

# Playwright
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
MAX_TENTATIVAS = int(os.getenv("MAX_TENTATIVAS", "3"))
TIMEOUT_PADRAO = int(os.getenv("TIMEOUT_PADRAO", "30000"))

# Storage State
STORAGE_STATE_DIR = Path(os.getenv("STORAGE_STATE_DIR", str(Path.home() / ".sog" / "auth")))
STORAGE_STATE_PJE = Path(os.getenv("STORAGE_STATE_PJE", str(STORAGE_STATE_DIR / "pje_storage.json")))
STORAGE_STATE_SISTJ = Path(os.getenv("STORAGE_STATE_SISTJ", str(STORAGE_STATE_DIR / "sistj_storage.json")))

# LLM (OpenAI) — usado como fallback quando regex não consegue extrair
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))


def init_config():
    """Inicializa configuração: carrega .env e cria diretórios necessários.
    
    Deve ser chamada explicitamente no startup da aplicação.
    """
    global DB_PATH, DADOS_DIR, SCREENSHOTS_DIR, DEMONSTRATIVOS_DIR

    load_dotenv(PROJECT_ROOT / ".env")

    # Recarrega DB_PATH após load_dotenv, pois pode ter mudado
    _db_path_env = os.getenv("DB_PATH", "")
    if _db_path_env:
        DB_PATH = _db_path_env
        # Se o path absoluto não for acessível (ex: /dados em dev local), fallback para relativo
        try:
            Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            DB_PATH = str(PROJECT_ROOT / "dados" / "custas.db")
    else:
        DB_PATH = str(PROJECT_ROOT / "dados" / "custas.db")

    DADOS_DIR = Path(DB_PATH).parent
    SCREENSHOTS_DIR = DADOS_DIR / "screenshots"
    DEMONSTRATIVOS_DIR = DADOS_DIR / "demonstrativos"

    # Cria diretórios se não existirem (silencioso se sem permissão)
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        DEMONSTRATIVOS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def validar_requisitos_homologacao_local() -> None:
    """Valida requisitos bloqueantes para homologação local do agente."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    chat_id = os.getenv("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
    faltantes = [
        nome
        for nome, valor in (
            ("TELEGRAM_BOT_TOKEN", token),
            ("TELEGRAM_CHAT_ID", chat_id),
        )
        if not valor
    ]
    if faltantes:
        raise RuntimeError(
            "Telegram obrigatório para homologação local: "
            + ", ".join(faltantes)
        )
