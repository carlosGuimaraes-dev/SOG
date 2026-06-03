"""
Schemas Pydantic para response models da API.
"""
from pydantic import BaseModel

from sog_shared.schemas import (
    AgenteComandoResponse,
    AgenteStatusResponse,
    AprovacaoResponse,
    BaixarPdfRequest,
    CicloAgenteResponse,
    CicloMembroResponse,
    CriarTarefaRequest,
    DadosProcessoResponse,
    DashboardSessoesResponse,
    DocumentoResponse,
    HistoricoItemResponse,
    LogResponse,
    ProcessoDetalheResponse,
    ProcessoListResponse,
    ProcessoResponse,
    RejeicaoRequest,
    RejeicaoResponse,
    SessaoStatusResponse,
    TarefaListResponse,
    TarefaResponse,
)


class ReprocessamentoRequest(BaseModel):
    motivo: str = ""


class ReprocessamentoResponse(BaseModel):
    message: str
    processo: ProcessoResponse


class LoginResponse(BaseModel):
    message: str


class TokenRefreshResponse(BaseModel):
    message: str


class LogoutResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    username: str


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
