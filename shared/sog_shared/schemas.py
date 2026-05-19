"""
Schemas Pydantic compartilhados entre API e Agente.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ProcessoResponse(BaseModel):
    id: int
    numero: str
    numero_sem_mascara: str
    status: str
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None
    tentativas: Optional[int] = None
    erro_msg: Optional[str] = None


class ProcessoListResponse(BaseModel):
    aguardando_aprovacao: List[ProcessoResponse]
    pendente_manual: List[ProcessoResponse]


class LogResponse(BaseModel):
    id: int
    processo_id: int
    etapa: str
    status: str
    mensagem: Optional[str] = None
    criado_em: Optional[str] = None


class DocumentoResponse(BaseModel):
    id: int
    processo_id: int
    doc_id: str
    tipo: str
    data_assinatura: Optional[str] = None
    nome: Optional[str] = None


class DadosProcessoResponse(BaseModel):
    id: Optional[int] = None
    processo_id: Optional[int] = None
    instancia: Optional[str] = None
    processo_eletronico: Optional[int] = None
    circunscricao: Optional[str] = None
    competencia: Optional[str] = None
    feito: Optional[str] = None
    classe: Optional[str] = None
    valor_causa: Optional[str] = None
    valor_causa_atualizado: Optional[str] = None
    data_distribuicao: Optional[str] = None
    polo_ativo: Optional[str] = None
    polo_passivo: Optional[str] = None
    tipo_guia: Optional[str] = None
    pro_rata: Optional[int] = None
    sucumbentes: Optional[Any] = None
    ids_oficios: Optional[str] = None
    ids_alvaras: Optional[str] = None
    ids_traslados: Optional[str] = None
    ids_mandados: Optional[str] = None
    ids_cartas_sentenca: Optional[str] = None
    ids_ar: Optional[str] = None
    ids_armp: Optional[str] = None
    ids_circunscricao_origem: Optional[str] = None
    ids_outra_circunscricao: Optional[str] = None
    outros_itens: Optional[Any] = None
    compensacao: Optional[Any] = None
    custas_pagas: Optional[Any] = None
    sucumbente_nome: Optional[str] = None
    sucumbente_cpf_cnpj: Optional[str] = None
    sucumbente_tipo: Optional[str] = None
    honorarios_percentual: Optional[str] = None
    suspensao_exigibilidade: Optional[int] = None
    valor_total_recolher: Optional[str] = None
    area_direito: Optional[str] = None
    obs_operador: Optional[str] = None
    screenshot_path: Optional[str] = None


class ProcessoDetalheResponse(BaseModel):
    processo: ProcessoResponse
    dados: Optional[DadosProcessoResponse] = None
    logs: List[LogResponse]
    documentos: List[DocumentoResponse]


class AprovacaoResponse(BaseModel):
    message: str


class RejeicaoResponse(BaseModel):
    message: str


class RejeicaoRequest(BaseModel):
    observacao: str = ""


class HistoricoItemResponse(BaseModel):
    id: int
    numero: str
    numero_sem_mascara: str
    status: str
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None
    tentativas: Optional[int] = None
    erro_msg: Optional[str] = None
    polo_ativo: Optional[str] = None
    valor_total_recolher: Optional[str] = None
    obs_operador: Optional[str] = None


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


class CriarTarefaRequest(BaseModel):
    tipo: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class BaixarPdfRequest(BaseModel):
    numero_processo: str = Field(
        ...,
        pattern=r"^\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}$",
    )


class TarefaResponse(BaseModel):
    id: int
    tipo: str
    status: str
    payload: Dict[str, Any]
    resultado: Optional[Dict[str, Any]] = None
    mensagem_erro: Optional[str] = None
    sistema_alvo: Optional[str] = None
    criado_por: Optional[str] = None
    criado_em: Optional[str] = None
    iniciado_em: Optional[str] = None
    concluido_em: Optional[str] = None
    atualizado_em: Optional[str] = None


class TarefaListResponse(BaseModel):
    total: int
    items: List[TarefaResponse]


class SessaoStatusResponse(BaseModel):
    sistema: str
    logado: bool
    mensagem: str
    ultima_verificacao: Optional[str] = None


class DashboardSessoesResponse(BaseModel):
    pje: SessaoStatusResponse
    sistj: SessaoStatusResponse
    agente_online: bool
    agente_status: str
    tarefas_pendentes: int
    tarefas_executando: int
