"""
Compatibilidade para o bootstrap runtime compartilhado.

Historicamente a refatoração runtime referenciava este módulo pelo nome.
O bootstrap canônico continua explícito e sem side-effects no import:
`sog_shared.config.init_config()` seguido de `sog_shared.infra_db.init_db()`.
"""

from sog_shared.config import init_config
from sog_shared.infra_db import SCHEMA_PATH, _garantir_schema_runtime, get_conn, init_db


def prepare_runtime() -> None:
    """Executa o bootstrap explícito de configuração e schema compartilhados."""
    init_config()
    init_db()


__all__ = [
    "SCHEMA_PATH",
    "_garantir_schema_runtime",
    "get_conn",
    "init_config",
    "init_db",
    "prepare_runtime",
]
