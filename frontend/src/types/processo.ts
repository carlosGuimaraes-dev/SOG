export interface Processo {
  id: number
  numero: string
  status: string
  criado_em: string
}

export interface ProcessoHistorico {
  id: number
  numero: string
  polo_ativo: string
  valor_total_recolher: string
  status: string
  atualizado_em: string
  obs_operador: string
}

export interface Sucumbente {
  percentual?: string | number
  '% ou Fração'?: string | number
  nome?: string
  cpf_cnpj?: string
  cpf?: string
  tipo?: string
}

export interface OutroItem {
  item_guia?: string
  itemGuia?: string
  item_calculo?: string
  itemCalculo?: string
  quantidade?: string | number
}

export interface CustasPaga {
  data?: string
  valor?: string
  numero_guia?: string
  numeroGuia?: string
}

export interface DadosProcesso {
  instancia?: string
  circunscricao?: string
  competencia?: string
  feito?: string
  classe?: string
  valor_causa?: string
  valor_causa_atualizado?: string
  data_distribuicao?: string
  polo_ativo?: string
  polo_passivo?: string
  tipo_guia?: string
  pro_rata?: boolean
  suspensao_exigibilidade?: boolean
  area_direito?: string
  sucumbentes?: Sucumbente[]
  ids_oficios?: string
  ids_alvaras?: string
  ids_traslados?: string
  ids_mandados?: string
  ids_cartas_sentenca?: string
  ids_ar?: string
  ids_armp?: string
  outros_itens?: OutroItem[]
  custas_pagas?: CustasPaga[]
  valor_total_recolher?: string
  screenshot_path?: string
  sucumbente_nome?: string
  obs_operador?: string
}

export interface ProcessoCompleto {
  processo: Processo
  dados: DadosProcesso
}
