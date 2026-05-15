"""
Configuração do agente de custas processuais TJDFT.
Lê variáveis de ambiente do .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# PJE
PJE_URL = os.getenv("PJE_URL", "https://pje.tjdft.jus.br")
PJE_USUARIO = os.getenv("PJE_USUARIO", "")
PJE_SENHA = os.getenv("PJE_SENHA", "")
PJE_ETIQUETA = os.getenv("PJE_ETIQUETA", "SHEILA DE DEUS (TREINAMENTO)")

# SISTJWEB
SISTJ_URL = os.getenv("SISTJ_URL", "https://sistj.tjdft.jus.br/sistj/sistj")
SISTJ_USUARIO = os.getenv("SISTJ_USUARIO", "")
SISTJ_SENHA = os.getenv("SISTJ_SENHA", "")

# Datajud API
DATAJUD_API_KEY = os.getenv("DATAJUD_API_KEY", "")
DATAJUD_URL = os.getenv(
    "DATAJUD_URL",
    "https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search",
)

# Dashboard
DASHBOARD_USUARIO = os.getenv("DASHBOARD_USUARIO", "admin")
DASHBOARD_SENHA_HASH = os.getenv("DASHBOARD_SENHA_HASH", "")

# Notificação
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORTA = int(os.getenv("SMTP_PORTA", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_SENHA = os.getenv("SMTP_SENHA", "")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "")

# Caminhos
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "dados" / "custas.db"))
DADOS_DIR = Path(DB_PATH).parent
SCREENSHOTS_DIR = DADOS_DIR / "screenshots"
DEMONSTRATIVOS_DIR = DADOS_DIR / "demonstrativos"

# Cria diretórios se não existirem (silencioso se sem permissão)
try:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DEMONSTRATIVOS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# Playwright
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
MAX_TENTATIVAS = int(os.getenv("MAX_TENTATIVAS", "3"))
TIMEOUT_PADRAO = int(os.getenv("TIMEOUT_PADRAO", "30000"))
