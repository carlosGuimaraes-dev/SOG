"""
Wrapper do banco de dados para a API.
Re-exporta tudo do pacote compartilhado sog_shared.db.
"""
from sog_shared.db import *  # noqa: F401,F403
from sog_shared.db import (  # noqa: F401
    COLUNAS_PERMITIDAS_DADOS_PROCESSO,
    salvar_dados_processo,
)
