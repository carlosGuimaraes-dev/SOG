"""Wrapper do banco de dados para o agente. Re-exporta do pacote compartilhado."""
from sog_shared.db import *  # noqa: F401,F403
from sog_shared.db import (  # noqa: F401
    COLUNAS_PERMITIDAS_DADOS_PROCESSO,
    salvar_dados_processo,
    init_db,
    get_conn,
    processo_existe,
    inserir_processo,
    atualizar_status,
    listar_pendentes,
    listar_aguardando_aprovacao,
    obter_dados_processo,
    salvar_documento,
    listar_documentos,
    registrar_log,
    listar_logs,
)
