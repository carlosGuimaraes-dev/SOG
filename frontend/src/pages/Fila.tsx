import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'
import Alert, { AlertDescription, AlertTitle } from '../components/ui/Alert'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs'
import AgenteStatusBar from '../components/agente/AgenteStatusBar'
import BuscaProcesso from '../components/fila/BuscaProcesso'
import PrioridadeBadge from '../components/fila/PrioridadeBadge'
import type { Processo } from '../types/processo'

interface DashboardSessoesResponse {
  agente_online: boolean
  agente_status: string
  tarefas_pendentes: number
  tarefas_executando: number
  pje: {
    sistema: string
    logado: boolean
    mensagem: string
  }
  sistj: {
    sistema: string
    logado: boolean
    mensagem: string
  }
}

function normalizarNumero(n: string): string {
  return n.replace(/\D/g, '')
}

function filtrarProcessos(processos: Processo[], busca: string): Processo[] {
  if (!busca.trim()) return processos
  const termo = normalizarNumero(busca)
  return processos.filter((p) => normalizarNumero(p.numero).includes(termo))
}

function formatarData(valor?: string): string {
  if (!valor) return '-'
  return new Date(valor).toLocaleString('pt-BR')
}

function StatusSessaoBadge({ logado }: { logado: boolean }) {
  return <Badge variant={logado ? 'success' : 'warning'}>{logado ? 'Sessão ativa' : 'Sessão pendente'}</Badge>
}

function StatCard({
  titulo,
  valor,
  descricao,
}: {
  titulo: string
  valor: string | number
  descricao: string
}) {
  return (
    <Card>
      <CardHeader className="space-y-2 pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">{titulo}</CardTitle>
        <div className="text-3xl font-semibold tracking-tight">{valor}</div>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{descricao}</CardContent>
    </Card>
  )
}

function ProcessoCard({ processo, manual }: { processo: Processo; manual: boolean }) {
  const destaqueClasse = processo.erro_msg
    ? 'border-destructive/50 bg-destructive/5'
    : manual
      ? 'border-warning/50 bg-warning/5'
      : ''

  return (
    <Card className={destaqueClasse}>
      <CardContent className="flex flex-col gap-4 py-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-lg font-semibold">{processo.numero}</div>
            {manual && <Badge variant="warning">Pendente manual</Badge>}
            <PrioridadeBadge processo={processo} />
            {processo.erro_msg && <Badge variant="destructive">Erro</Badge>}
          </div>

          <div className="grid gap-3 text-sm text-muted-foreground md:grid-cols-2">
            <div>
              <span className="font-medium text-foreground">Polo ativo:</span>{' '}
              {processo.polo_ativo || '-'}
            </div>
            <div>
              <span className="font-medium text-foreground">Valor total:</span>{' '}
              {processo.valor_total_recolher || '-'}
            </div>
            <div>
              <span className="font-medium text-foreground">Criado em:</span>{' '}
              {formatarData(processo.criado_em)}
            </div>
            <div>
              <span className="font-medium text-foreground">Atualizado em:</span>{' '}
              {formatarData(processo.atualizado_em || processo.criado_em)}
            </div>
          </div>

          {manual ? (
            <p className="text-sm text-muted-foreground">
              Requer conferência manual dos itens da guia antes da aprovação.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              Revisão operacional obrigatória antes de liberar emissão no SISTJWEB.
            </p>
          )}

          {processo.tentativas !== undefined && processo.tentativas > 0 && (
            <div className="text-sm text-muted-foreground">Tentativas: {processo.tentativas}</div>
          )}
        </div>

        <Link to={`/detalhe/${processo.id}`} aria-label={`Revisar processo ${processo.numero}`} className="lg:self-center">
          <Button variant={manual ? 'outline' : 'default'}>Revisar</Button>
        </Link>
      </CardContent>
    </Card>
  )
}

export default function Fila() {
  const [aguardando, setAguardando] = useState<Processo[]>([])
  const [manual, setManual] = useState<Processo[]>([])
  const [sessoes, setSessoes] = useState<DashboardSessoesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [busca, setBusca] = useState('')
  const [abaAtiva, setAbaAtiva] = useState<'aguardando' | 'manual'>('aguardando')
  const { addToast } = useToast()

  async function fetchData() {
    const [processosRes, sessoesRes] = await Promise.allSettled([
      api.get(ENDPOINTS.PROCESSOS),
      api.get(ENDPOINTS.DASHBOARD_SESSOES),
    ])

    if (processosRes.status === 'fulfilled') {
      setAguardando(processosRes.value.data.aguardando_aprovacao || [])
      setManual(processosRes.value.data.pendente_manual || [])
    } else {
      addToast('Erro ao carregar processos', 'error')
    }

    if (sessoesRes.status === 'fulfilled') {
      setSessoes(sessoesRes.value.data)
    } else {
      addToast('Erro ao carregar resumo operacional', 'error')
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const aguardandoFiltrado = useMemo(() => filtrarProcessos(aguardando, busca), [aguardando, busca])
  const manualFiltrado = useMemo(() => filtrarProcessos(manual, busca), [manual, busca])
  const nenhumResultado = busca.trim() !== '' && aguardandoFiltrado.length === 0 && manualFiltrado.length === 0
  const totalNaFila = aguardando.length + manual.length
  const totalCritico = aguardando.filter((processo) => Boolean(processo.erro_msg)).length
    + manual.filter((processo) => Boolean(processo.erro_msg)).length

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Dashboard operacional
            </p>
            <h2 className="text-3xl font-semibold tracking-tight">Controle de custas para revisão final</h2>
            <p className="max-w-3xl text-sm text-muted-foreground">
              A fila separa processos prontos para revisão e casos com pendência manual. A aprovação só deve ocorrer após conferência explícita dos dados exibidos.
            </p>
          </div>
          <Badge variant={totalCritico > 0 ? 'destructive' : 'secondary'} className="w-fit">
            {totalCritico > 0 ? `${totalCritico} processo(s) com erro anterior` : 'Sem erros pendentes na fila'}
          </Badge>
        </div>

        {manual.length > 0 && (
          <Alert variant="warning">
            <AlertTitle>Pendências manuais exigem conferência explícita</AlertTitle>
            <AlertDescription>
              {manual.length} processo(s) dependem de validação manual dos itens da guia antes de qualquer aprovação.
            </AlertDescription>
          </Alert>
        )}
      </section>

      <AgenteStatusBar />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          titulo="Processos na fila"
          valor={totalNaFila}
          descricao={`${aguardando.length} aguardando aprovação e ${manual.length} com pendência manual.`}
        />
        <StatCard
          titulo="Tarefas do agente"
          valor={`${sessoes?.tarefas_executando ?? 0}/${sessoes?.tarefas_pendentes ?? 0}`}
          descricao="Executando / pendentes no orquestrador."
        />
        <Card>
          <CardHeader className="space-y-2 pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sessão PJE</CardTitle>
            <div className="flex items-center gap-2">
              <StatusSessaoBadge logado={Boolean(sessoes?.pje.logado)} />
              <span className="text-sm text-muted-foreground">{sessoes?.pje.mensagem || 'Sem leitura disponível'}</span>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Estado exposto pelo backend de monitoramento.</CardContent>
        </Card>
        <Card>
          <CardHeader className="space-y-2 pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sessão SISTJWEB</CardTitle>
            <div className="flex items-center gap-2">
              <StatusSessaoBadge logado={Boolean(sessoes?.sistj.logado)} />
              <span className="text-sm text-muted-foreground">{sessoes?.sistj.mensagem || 'Sem leitura disponível'}</span>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {sessoes?.agente_online ? `Agente online em status ${sessoes.agente_status}.` : 'Agente sem heartbeat recente.'}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <h3 className="text-xl font-semibold">Fila de revisão</h3>
            <p className="text-sm text-muted-foreground">
              Pesquise pelo número do processo e alterne entre os conjuntos auditáveis da operação.
            </p>
          </div>
          <div className="w-full lg:max-w-md">
            <BuscaProcesso valor={busca} onChange={setBusca} />
          </div>
        </div>

        <Tabs value={abaAtiva} onValueChange={(valor) => setAbaAtiva(valor as 'aguardando' | 'manual')} className="space-y-4">
          <TabsList>
            <TabsTrigger value="aguardando">
              Aguardando aprovação
              <span className="ml-2 rounded-full bg-background px-2 py-0.5 text-xs text-muted-foreground">
                {aguardandoFiltrado.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="manual">
              Pendência manual
              <span className="ml-2 rounded-full bg-background px-2 py-0.5 text-xs text-muted-foreground">
                {manualFiltrado.length}
              </span>
            </TabsTrigger>
          </TabsList>

          {nenhumResultado && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Nenhum processo encontrado para esta busca.
              </CardContent>
            </Card>
          )}

          <TabsContent value="aguardando" className="space-y-4">
            {aguardandoFiltrado.length === 0 ? (
              !nenhumResultado && (
                <Card>
                  <CardContent className="py-8 text-center text-muted-foreground">
                    Nenhum processo aguardando aprovação.
                  </CardContent>
                </Card>
              )
            ) : (
              <div className="grid gap-4">
                {aguardandoFiltrado.map((processo) => (
                  <ProcessoCard key={processo.id} processo={processo} manual={false} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="manual" className="space-y-4">
            {manualFiltrado.length === 0 ? (
              !nenhumResultado && (
                <Card>
                  <CardContent className="py-8 text-center text-muted-foreground">
                    Nenhum processo pendente manual.
                  </CardContent>
                </Card>
              )
            ) : (
              <div className="grid gap-4">
                {manualFiltrado.map((processo) => (
                  <ProcessoCard key={processo.id} processo={processo} manual />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </section>
    </div>
  )
}
