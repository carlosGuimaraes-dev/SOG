"""
Schemas Pydantic para response models da API.
"""
from pydantic import BaseModel

from sog_shared import schemas as shared_schemas

AgenteComandoResponse = shared_schemas.AgenteComandoResponse
AgenteStatusResponse = shared_schemas.AgenteStatusResponse
AprovacaoResponse = shared_schemas.AprovacaoResponse
BaixarPdfRequest = shared_schemas.BaixarPdfRequest
CicloAgenteResponse = shared_schemas.CicloAgenteResponse
CicloMembroResponse = shared_schemas.CicloMembroResponse
CriarTarefaRequest = shared_schemas.CriarTarefaRequest
DadosProcessoResponse = shared_schemas.DadosProcessoResponse
DashboardSessoesResponse = shared_schemas.DashboardSessoesResponse
DocumentoResponse = shared_schemas.DocumentoResponse
HistoricoItemResponse = shared_schemas.HistoricoItemResponse
LogResponse = shared_schemas.LogResponse
ProcessoDetalheResponse = shared_schemas.ProcessoDetalheResponse
ProcessoListResponse = shared_schemas.ProcessoListResponse
ProcessoResponse = shared_schemas.ProcessoResponse
RejeicaoRequest = shared_schemas.RejeicaoRequest
RejeicaoResponse = shared_schemas.RejeicaoResponse
SessaoStatusResponse = shared_schemas.SessaoStatusResponse
TarefaListResponse = shared_schemas.TarefaListResponse
TarefaResponse = shared_schemas.TarefaResponse

__all__ = [
    "AgenteComandoResponse",
    "AgenteStatusResponse",
    "AprovacaoResponse",
    "BaixarPdfRequest",
    "CicloAgenteResponse",
    "CicloMembroResponse",
    "CriarTarefaRequest",
    "DadosProcessoResponse",
    "DashboardSessoesResponse",
    "DocumentoResponse",
    "HealthResponse",
    "HistoricoItemResponse",
    "LogResponse",
    "LoginResponse",
    "LogoutResponse",
    "MeResponse",
    "ProcessoDetalheResponse",
    "ProcessoListResponse",
    "ProcessoResponse",
    "RejeicaoRequest",
    "RejeicaoResponse",
    "ReprocessamentoRequest",
    "ReprocessamentoResponse",
    "SessaoStatusResponse",
    "TarefaListResponse",
    "TarefaResponse",
    "TokenRefreshResponse",
]


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
    auth_required: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
