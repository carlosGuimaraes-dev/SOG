import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import AgenteStatusBar from '../components/agente/AgenteStatusBar'
import Alert, { AlertDescription, AlertTitle } from '../components/ui/Alert'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import { useToast } from '../components/ToastProvider'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import type { Processo } from '../types/processo'

interface DashboardSessoesResponse {
  agente_online: boolean
  agente_status: string
  tarefas_pendentes: number
  tarefas_executando: number
  pje: {
    logado: boolean
    mensagem: string
  }
  sistj: {
    logado: boolean
    mensagem: string
  }
}

interface CicloMembro {
  id: number
  processo_id: number
  numero: string
  origem: string
  status_snapshot: string
  status_atual?: string | null
  criado_em?: string
}

interface CicloAtualResponse {
  uuid: string
  rotulo: string
  status: string
  total_membros: number
  total_novos: number
  total_rearmados: number
  total_concluidos: number
  total_erros: number
  erro_msg?: string | null
  membros: CicloMembro[]
}

interface ProcessosResponse {
  aguardando_aprovacao: Processo[]
  pendente_manual: Processo[]
}

interface LinhaOperacional {
  membroId: number
  processoId: number
  numero: string
  origem: string
  statusSnapshot: string
  statusAtual: string
  criadoEm?: string
  valorTotal?: string
  tentativas?: number
  erroMsg?: string
  reprocessarSolicitadoEm?: string
}

interface StatusVisual {
  label: string
  className: string
}

interface AcaoContextual {
  label: string
  variant: 'default' | 'outline'
  disabled?: boolean
}

type AddToast = (message: string, variant?: 'success' | 'error' | 'info') => void

const resumoGuiaPorStatus: Record<string, string> = {
  pendente_manual: 'Itens da guia exigem conferência manual',
  erro: 'Guia bloqueada por falha operacional',
  rejeitado: 'Guia rejeitada e fora do fluxo automático',
  aprovado: 'Guia enviada para emissão no SISTJWEB',
  emitido: 'Guia emitida e consolidada no ciclo',
  pendente: 'Guia ainda em preenchimento automático',
}

function formatarData(valor?: string): string {
  if (!valor) return '-'
  return new Date(valor).toLocaleString('pt-BR')
}

function formatarTempoRelativo(valor?: string): string {
  if (!valor) return '-'

  const diffMs = Date.now() - new Date(valor).getTime()
  if (Number.isNaN(diffMs)) return '-'

  const diffMin = Math.max(0, Math.floor(diffMs / 60000))
  if (diffMin < 1) return 'Agora'
  if (diffMin < 60) return `${diffMin} min`

  const diffHoras = Math.floor(diffMin / 60)
  if (diffHoras < 24) return `${diffHoras} h`

  const diffDias = Math.floor(diffHoras / 24)
  return `${diffDias} d`
}

function obterVisualStatus(status: string): StatusVisual {
  switch (status) {
    case 'aguardando_aprovacao':
      return { label: 'Aguardando aprovação', className: 'bg-sky-100 text-sky-900 border-sky-200' }
    case 'pendente_manual':
      return { label: 'Pendência manual', className: 'bg-amber-100 text-amber-900 border-amber-200' }
    case 'emitido':
      return { label: 'Emitido', className: 'bg-emerald-100 text-emerald-900 border-emerald-200' }
    case 'erro':
      return { label: 'Erro', className: 'bg-red-100 text-red-900 border-red-200' }
    case 'rejeitado':
      return { label: 'Rejeitado', className: 'bg-red-50 text-red-800 border-red-100' }
    case 'aprovado':
      return { label: 'Aprovado', className: 'bg-slate-100 text-slate-800 border-slate-200' }
    case 'pendente':
      return { label: 'Em processamento', className: 'bg-slate-100 text-slate-700 border-slate-200' }
    default:
      return { label: status.replace(/_/g, ' '), className: 'bg-slate-100 text-slate-700 border-slate-200' }
  }
}

function obterEtapaAtual(linha: LinhaOperacional): string {
  switch (linha.statusAtual) {
    case 'aguardando_aprovacao':
      return 'Conferência final do operador'
    case 'pendente_manual':
      return linha.reprocessarSolicitadoEm ? 'Aguardando próximo ciclo' : 'Validação manual dos itens'
    case 'erro':
      return 'Falha operacional no ciclo'
    case 'rejeitado':
      return 'Ajuste após rejeição'
    case 'aprovado':
      return 'Emissão em andamento'
    case 'emitido':
      return 'Emissão concluída'
    case 'pendente':
      return linha.origem === 'rearmado' ? 'Reentrada do processo no lote' : 'Coleta inicial pelo agente'
    default:
      return 'Acompanhamento operacional'
  }
}

function obterResumoGuia(linha: LinhaOperacional): string {
  if (linha.erroMsg) return linha.erroMsg
  if (linha.reprocessarSolicitadoEm) return 'Reprocessamento já solicitado'
  if (linha.statusAtual === 'aguardando_aprovacao') {
    return linha.valorTotal ? `Guia pronta: ${linha.valorTotal}` : 'Guia pronta para liberar emissão'
  }
  return resumoGuiaPorStatus[linha.statusAtual] || 'Sem leitura adicional da guia'
}

function obterAcaoContextual(linha: LinhaOperacional): AcaoContextual {
  if (linha.statusAtual === 'aguardando_aprovacao') {
    return { label: 'Revisar aprovação', variant: 'default' }
  }

  if (linha.reprocessarSolicitadoEm && ['pendente_manual', 'erro', 'rejeitado'].includes(linha.statusAtual)) {
    return { label: 'Reprocessamento solicitado', variant: 'outline', disabled: true }
  }
  if (linha.statusAtual === 'pendente_manual') return { label: 'Validar pendência', variant: 'outline' }
  if (linha.statusAtual === 'erro' || linha.statusAtual === 'rejeitado') {
    return { label: 'Solicitar reprocessamento', variant: 'outline' }
  }
  if (linha.statusAtual === 'emitido') return { label: 'Ver emissão', variant: 'outline' }
  return { label: 'Acompanhar', variant: 'outline' }
}

function montarLinhasOperacionais(ciclo: CicloAtualResponse | null, processos: ProcessosResponse | null): LinhaOperacional[] {
  const filas = [...(processos?.aguardando_aprovacao || []), ...(processos?.pendente_manual || [])]
  const processosPorId = new Map(filas.map((processo) => [processo.id, processo]))

  return (ciclo?.membros || []).map((membro) => montarLinhaOperacional(membro, processosPorId.get(membro.processo_id)))
}

function montarLinhaOperacional(membro: CicloMembro, processo?: Processo): LinhaOperacional {
  return {
    membroId: membro.id,
    processoId: membro.processo_id,
    numero: membro.numero,
    origem: membro.origem,
    statusSnapshot: membro.status_snapshot,
    statusAtual: membro.status_atual || membro.status_snapshot,
    criadoEm: obterDataOperacional(membro, processo),
    valorTotal: processo?.valor_total_recolher,
    tentativas: processo?.tentativas,
    erroMsg: processo?.erro_msg,
    reprocessarSolicitadoEm: processo?.reprocessar_solicitado_em,
  }
}

function obterDataOperacional(membro: CicloMembro, processo?: Processo): string | undefined {
  return processo?.atualizado_em || processo?.criado_em || membro.criado_em
}

function contarProcessosCriticos(linhas: LinhaOperacional[]): number {
  return linhas.filter((linha) => linha.statusAtual === 'erro' || linha.statusAtual === 'pendente_manual').length
}

function useCicloAtualDados(addToast: AddToast) {
  const [ciclo, setCiclo] = useState<CicloAtualResponse | null>(null)
  const [processos, setProcessos] = useState<ProcessosResponse | null>(null)
  const [sessoes, setSessoes] = useState<DashboardSessoesResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      await carregarDadosCiclo(setCiclo, setProcessos, setSessoes, addToast)
      setLoading(false)
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [addToast])

  return { ciclo, processos, sessoes, loading }
}

async function carregarDadosCiclo(
  setCiclo: (ciclo: CicloAtualResponse | null) => void,
  setProcessos: (processos: ProcessosResponse) => void,
  setSessoes: (sessoes: DashboardSessoesResponse) => void,
  addToast: AddToast,
) {
  const [cicloRes, processosRes, sessoesRes] = await Promise.allSettled([
    api.get<CicloAtualResponse | null>(ENDPOINTS.AGENTE_CICLO_ATUAL),
    api.get<ProcessosResponse>(ENDPOINTS.PROCESSOS),
    api.get<DashboardSessoesResponse>(ENDPOINTS.DASHBOARD_SESSOES),
  ])

  aplicarResultadoCiclo(cicloRes, setCiclo, addToast)
  aplicarResultadoProcessos(processosRes, setProcessos, addToast)
  aplicarResultadoSessoes(sessoesRes, setSessoes, addToast)
}

function aplicarResultadoCiclo(
  resultado: PromiseSettledResult<{ data: CicloAtualResponse | null }>,
  setCiclo: (ciclo: CicloAtualResponse | null) => void,
  addToast: AddToast,
) {
  if (resultado.status === 'fulfilled') setCiclo(resultado.value.data)
  else addToast('Erro ao carregar o ciclo atual do agente', 'error')
}

function aplicarResultadoProcessos(
  resultado: PromiseSettledResult<{ data: ProcessosResponse }>,
  setProcessos: (processos: ProcessosResponse) => void,
  addToast: AddToast,
) {
  if (resultado.status === 'fulfilled') setProcessos(resultado.value.data)
  else addToast('Erro ao carregar processos do ciclo atual', 'error')
}

function aplicarResultadoSessoes(
  resultado: PromiseSettledResult<{ data: DashboardSessoesResponse }>,
  setSessoes: (sessoes: DashboardSessoesResponse) => void,
  addToast: AddToast,
) {
  if (resultado.status === 'fulfilled') setSessoes(resultado.value.data)
  else addToast('Erro ao carregar resumo operacional', 'error')
}

function CicloAtualSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-10 w-72" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-72 w-full" />
    </div>
  )
}

function CicloAtualHeader({ processosCriticos }: { processosCriticos: number }) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <CicloAtualTitulos />
      <CicloAtualAcoes processosCriticos={processosCriticos} />
    </div>
  )
}

function CicloAtualTitulos() {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">Ciclo atual</p>
      <h2 className="text-3xl font-semibold tracking-tight">Acompanhamento operacional da emissão</h2>
      <p className="max-w-3xl text-sm text-muted-foreground">Eu preciso acrescentar subtitulo aqui.</p>
    </div>
  )
}

function CicloAtualAcoes({ processosCriticos }: { processosCriticos: number }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge variant={processosCriticos > 0 ? 'destructive' : 'secondary'}>
        {processosCriticos > 0 ? `${processosCriticos} processo(s) exigem ação explícita` : 'Sem pendência crítica no lote'}
      </Badge>
      <Link to="/processos">
        <Button variant="outline">Abrir fila completa</Button>
      </Link>
    </div>
  )
}

function CicloAtualAlertas({ ciclo }: { ciclo: CicloAtualResponse | null }) {
  return (
    <>
      {!ciclo && (
        <Alert>
          <AlertTitle>Nenhum ciclo ativo no momento</AlertTitle>
          <AlertDescription>
            O agente não publicou um lote atual. Use a barra do agente para iniciar ou retomar um ciclo antes de revisar processos nesta tela.
          </AlertDescription>
        </Alert>
      )}

      {ciclo?.erro_msg && (
        <Alert variant="warning">
          <AlertTitle>Ciclo com alerta registrado</AlertTitle>
          <AlertDescription>{ciclo.erro_msg}</AlertDescription>
        </Alert>
      )}
    </>
  )
}

function ResumoCicloCards({ ciclo, sessoes }: { ciclo: CicloAtualResponse | null; sessoes: DashboardSessoesResponse | null }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <CardResumoLote ciclo={ciclo} />
      <CardResultadoCiclo ciclo={ciclo} />
      <CardSessaoPje sessoes={sessoes} />
      <CardSessaoSistj sessoes={sessoes} />
    </section>
  )
}

function CardResumoLote({ ciclo }: { ciclo: CicloAtualResponse | null }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">Lote do ciclo</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold">{ciclo?.total_membros ?? 0}</div>
        <p className="text-sm text-muted-foreground">
          {ciclo?.total_novos ?? 0} novos do PJE e {ciclo?.total_rearmados ?? 0} rearmados.
        </p>
      </CardContent>
    </Card>
  )
}

function CardResultadoCiclo({ ciclo }: { ciclo: CicloAtualResponse | null }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">Resultado do ciclo</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold">{ciclo?.total_concluidos ?? 0}</div>
        <p className="text-sm text-muted-foreground">
          {ciclo?.total_erros ?? 0} com erro e status do lote em {ciclo?.status || 'sem ciclo'}.
        </p>
      </CardContent>
    </Card>
  )
}

function CardSessaoPje({ sessoes }: { sessoes: DashboardSessoesResponse | null }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">Sessão PJE</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Badge variant={sessoes?.pje.logado ? 'success' : 'warning'}>
          {sessoes?.pje.logado ? 'Sessão ativa' : 'Sessão pendente'}
        </Badge>
        <p className="text-sm text-muted-foreground">{sessoes?.pje.mensagem || 'Sem leitura disponível.'}</p>
      </CardContent>
    </Card>
  )
}

function CardSessaoSistj({ sessoes }: { sessoes: DashboardSessoesResponse | null }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">Sessão SISTJWEB</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Badge variant={sessoes?.sistj.logado ? 'success' : 'warning'}>
          {sessoes?.sistj.logado ? 'Sessão ativa' : 'Sessão pendente'}
        </Badge>
        <p className="text-sm text-muted-foreground">
          {sessoes?.agente_online ? `Agente online em status ${sessoes.agente_status}.` : 'Agente sem heartbeat recente.'}
        </p>
      </CardContent>
    </Card>
  )
}

function TabelaCicloCard({ ciclo, linhas }: { ciclo: CicloAtualResponse | null; linhas: LinhaOperacional[] }) {
  return (
    <section className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <CardTitle>Tabela operacional do ciclo</CardTitle>
            <p className="text-sm text-muted-foreground">
              Eu preciso alterar mensagem aqui!.
            </p>
          </div>
          {ciclo && <Badge variant="outline">{ciclo.rotulo}</Badge>}
        </CardHeader>
        <CardContent className="p-0">
          <TabelaOperacional linhas={linhas} />
        </CardContent>
      </Card>
    </section>
  )
}

function LinhaTabelaOperacional({ linha }: { linha: LinhaOperacional }) {
  const acao = obterAcaoContextual(linha)
  const statusAtual = obterVisualStatus(linha.statusAtual)
  const statusEntrada = obterVisualStatus(linha.statusSnapshot)
  const tempoBase = linha.reprocessarSolicitadoEm || linha.criadoEm

  return (
    <tr key={linha.membroId} className="border-b last:border-0">
      <CelulaProcesso linha={linha} />
      <CelulaStatus statusAtual={statusAtual} statusEntrada={statusEntrada} />
      <CelulaEtapa linha={linha} />
      <td className="px-4 py-3 align-top text-muted-foreground">{obterResumoGuia(linha)}</td>
      <CelulaTempo tempoBase={tempoBase} />
      <CelulaAcao linha={linha} acao={acao} />
    </tr>
  )
}

function CelulaProcesso({ linha }: { linha: LinhaOperacional }) {
  const tentativasResumo = linha.tentativas && linha.tentativas > 0 ? ` · ${linha.tentativas} tentativa(s)` : ''

  return (
    <td className="px-4 py-3 align-top">
      <div className="font-medium">{linha.numero}</div>
      <div className="text-xs text-muted-foreground">
        {linha.origem === 'rearmado' ? 'Rearmado no ciclo' : 'Novo do PJE'}
        {tentativasResumo}
      </div>
    </td>
  )
}

function CelulaStatus({ statusAtual, statusEntrada }: { statusAtual: StatusVisual; statusEntrada: StatusVisual }) {
  return (
    <td className="px-4 py-3 align-top">
      <div className="space-y-1">
        <Badge variant="outline" className={statusAtual.className}>{statusAtual.label}</Badge>
        <div className="text-xs text-muted-foreground">Entrada: {statusEntrada.label}</div>
      </div>
    </td>
  )
}

function CelulaEtapa({ linha }: { linha: LinhaOperacional }) {
  return (
    <td className="px-4 py-3 align-top">
      <div className="font-medium text-foreground">{obterEtapaAtual(linha)}</div>
      <div className="text-xs text-muted-foreground">{formatarData(linha.criadoEm)}</div>
    </td>
  )
}

function CelulaTempo({ tempoBase }: { tempoBase?: string }) {
  return (
    <td className="px-4 py-3 align-top">
      <div className="font-medium">{formatarTempoRelativo(tempoBase)}</div>
      <div className="text-xs text-muted-foreground">{formatarData(tempoBase)}</div>
    </td>
  )
}

function CelulaAcao({ linha, acao }: { linha: LinhaOperacional; acao: AcaoContextual }) {
  return (
    <td className="px-4 py-3 text-right align-top">
      <Link to={`/detalhe/${linha.processoId}`} aria-label={`${acao.label} do processo ${linha.numero}`} className="inline-flex">
        <Button size="sm" variant={acao.variant} disabled={acao.disabled}>{acao.label}</Button>
      </Link>
    </td>
  )
}

function TabelaOperacional({ linhas }: { linhas: LinhaOperacional[] }) {
  if (linhas.length === 0) {
    return <TabelaVazia />
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[960px] text-sm">
        <CabecalhoTabelaOperacional />
        <tbody>
          {linhas.map((linha) => <LinhaTabelaOperacional key={linha.membroId} linha={linha} />)}
        </tbody>
      </table>
    </div>
  )
}

function TabelaVazia() {
  return (
    <Card>
      <CardContent className="px-6 py-8 text-sm text-muted-foreground">
        Nenhum processo vinculado ao ciclo atual.
      </CardContent>
    </Card>
  )
}

function CabecalhoTabelaOperacional() {
  return (
    <thead>
      <tr className="border-b bg-muted/40">
        <th className="px-4 py-3 text-left font-medium">Processo</th>
        <th className="px-4 py-3 text-left font-medium">Status</th>
        <th className="px-4 py-3 text-left font-medium">Etapa atual</th>
        <th className="px-4 py-3 text-left font-medium">Guia</th>
        <th className="px-4 py-3 text-left font-medium">Tempo</th>
        <th className="px-4 py-3 text-right font-medium">Ação</th>
      </tr>
    </thead>
  )
}

export default function CicloAtual() {
  const { addToast } = useToast()
  const { ciclo, processos, sessoes, loading } = useCicloAtualDados(addToast)
  const linhasOperacionais = useMemo(() => montarLinhasOperacionais(ciclo, processos), [ciclo, processos])
  const processosCriticos = contarProcessosCriticos(linhasOperacionais)

  if (loading) {
    return <CicloAtualSkeleton />
  }

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <CicloAtualHeader processosCriticos={processosCriticos} />
        <CicloAtualAlertas ciclo={ciclo} />
      </section>

      <AgenteStatusBar />
      <ResumoCicloCards ciclo={ciclo} sessoes={sessoes} />
      <TabelaCicloCard ciclo={ciclo} linhas={linhasOperacionais} />
    </div>
  )
}
