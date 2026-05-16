import os
import sys
from pathlib import Path

# Adiciona api/src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Adiciona shared/ ao path para importar sog_shared sem instalação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

# Variáveis obrigatórias para os testes
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-com-mais-de-32-caracteres!")

# Gera um hash bcrypt válido para que a validação de startup não falhe
import bcrypt  # noqa: E402
_test_hash = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode()
os.environ.setdefault("DASHBOARD_SENHA_HASH", _test_hash)
