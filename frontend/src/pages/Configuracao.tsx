import { useCallback, useEffect, useState } from 'react'
import AgenteStatusBar from '../components/agente/AgenteStatusBar'
import Alert, { AlertDescription, AlertTitle } from '../components/ui/Alert'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import { useToast } from '../components/ToastProvider'
import api from '../lib/api'
import { useAuth } from '../lib/auth'
import { ENDPOINTS } from '../lib/endpoints'

const PJE_URL = 'https://pje.tjdft.jus.br/pje/login.seam'
const SISTJWEB_URL = 'https://sistj.tjdft.jus.br/sistj/sistj'

interface SessaoDashboard {
  sistema: string
  logado: boolean
  mensagem: string
  ultima_verificacao?: string | null
}

interface DashboardSessoesResponse {
  agente_online: boolean
  agente_status: string
  tarefas_pendentes: number
  tarefas_executando: number
  pje: SessaoDashboard
  sistj: SessaoDashboard
}

interface AgenteStatusResponse {
  status: string
  mensagem: string
  online: boolean
  atualizado_em?: string | null
  pode_iniciar?: boolean
  pode_parar?: boolean
  relogin_required?: boolean
}

function formatarData(valor?: string | null): string {
  if (!valor) return 'Sem leitura disponível'
  const data = new Date(valor)
  if (Number.isNaN(data.getTime())) return 'Sem leitura disponível'
  return data.toLocaleString('pt-BR')
}

function StatusSessaoCard({
  titulo,
  descricao,
  status,
  onAbrir,
  onReautenticar,
  reautenticando,
}: {
  titulo: string
  descricao: string
  status: SessaoDashboard
  onAbrir: () => void
  onReautenticar: () => Promise<void>
  reautenticando: boolean
}) {
  const ativo = status.logado

  return (
    <Card>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <CardTitle>{titulo}</CardTitle>
            <p className="text-sm text-muted-foreground">{descricao}</p>
          </div>
          <Badge variant={ativo ? 'success' : 'warning'}>
            {ativo ? 'Sessão ativa' : 'Sessão pendente'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Status lido</dt>
            <dd className="mt-1 font-medium text-foreground">{status.mensagem}</dd>
          </div>
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Última verificação</dt>
            <dd className="mt-1 font-medium text-foreground">{formatarData(status.ultima_verificacao)}</dd>
          </div>
        </dl>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button type="button" onClick={onAbrir}>
            Abrir {titulo}
          </Button>
          <Button type="button" variant="outline" onClick={onReautenticar} disabled={reautenticando}>
            {reautenticando ? 'Solicitando...' : 'Solicitar reautenticação'}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          {ativo
            ? `Use esta ação apenas quando precisar revisar manualmente a sessão do ${titulo}.`
            : `Abra o ${titulo}, conclua o login manual e retome o ciclo quando o agente sinalizar reautenticação concluída.`}
        </p>
      </CardContent>
    </Card>
  )
}

export default function Configuracao() {
  const { addToast } = useToast()
  const { authRequired } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardSessoesResponse | null>(null)
  const [agente, setAgente] = useState<AgenteStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pendingReauth, setPendingReauth] = useState<'pje' | 'sistj' | null>(null)

  const carregar = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [dashboardRes, agenteRes] = await Promise.all([
        api.get<DashboardSessoesResponse>(ENDPOINTS.DASHBOARD_SESSOES),
        api.get<AgenteStatusResponse>(ENDPOINTS.AGENTE_STATUS),
      ])
      setDashboard(dashboardRes.data)
      setAgente(agenteRes.data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível carregar a configuração operacional.')
      setDashboard(null)
      setAgente(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  function abrirSistema(url: string, nome: string) {
    window.open(url, '_blank', 'noopener,noreferrer')
    addToast(`${nome} aberto em nova aba do navegador local.`, 'info')
  }

  async function solicitarReautenticacao(sistema: 'pje' | 'sistj') {
    const endpoint = sistema === 'pje' ? ENDPOINTS.PJE_REAUTENTICAR : ENDPOINTS.SISTJ_REAUTENTICAR
    const label = sistema === 'pje' ? 'PJe' : 'SISTJWEB'

    setPendingReauth(sistema)
    try {
      await api.post(endpoint)
      addToast(`Reautenticação de ${label} solicitada para o agente.`, 'success')
      await carregar()
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      addToast(detail || `Não foi possível solicitar reautenticação de ${label}.`, 'error')
    } finally {
      setPendingReauth(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Configuração operacional</h2>
        <p className="text-sm text-muted-foreground">
          Abra sistemas externos, acompanhe o estado do runtime local e conduza reautenticação sem sair do dashboard.
        </p>
      </div>

      <AgenteStatusBar />

      {!authRequired && (
        <Alert>
          <AlertTitle>Dashboard local sem login próprio</AlertTitle>
          <AlertDescription>
            Este ambiente opera em modo local. O acesso ao dashboard não exige credenciais próprias; PJe e SISTJWEB continuam com autenticação manual independente.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Falha ao carregar a aba de configuração</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end">
        <Button type="button" variant="outline" onClick={carregar} disabled={loading}>
          {loading ? 'Atualizando...' : 'Atualizar status'}
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-56 w-full lg:col-span-2" />
        </div>
      ) : dashboard ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <StatusSessaoCard
            titulo="PJe"
            descricao="Abertura e validação independentes da sessão do tribunal."
            status={dashboard.pje}
            onAbrir={() => abrirSistema(PJE_URL, 'PJe')}
            onReautenticar={() => solicitarReautenticacao('pje')}
            reautenticando={pendingReauth === 'pje'}
          />
          <StatusSessaoCard
            titulo="SISTJWEB"
            descricao="Sessão operacional separada para preenchimento e emissão."
            status={dashboard.sistj}
            onAbrir={() => abrirSistema(SISTJWEB_URL, 'SISTJWEB')}
            onReautenticar={() => solicitarReautenticacao('sistj')}
            reautenticando={pendingReauth === 'sistj'}
          />

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Diagnóstico do runtime local</CardTitle>
              <p className="text-sm text-muted-foreground">
                Estado útil para operação e suporte: agente, fila local e necessidade de relogin.
              </p>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Agente</div>
                <div className="mt-1 font-medium text-foreground">
                  {dashboard.agente_online ? 'Online' : 'Offline'}
                </div>
                <div className="text-sm text-muted-foreground">{dashboard.agente_status}</div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Tarefas pendentes</div>
                <div className="mt-1 text-2xl font-semibold text-foreground">{dashboard.tarefas_pendentes}</div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Tarefas executando</div>
                <div className="mt-1 text-2xl font-semibold text-foreground">{dashboard.tarefas_executando}</div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Autenticação do dashboard</div>
                <div className="mt-1 font-medium text-foreground">{authRequired ? 'Protegida' : 'Dispensada'}</div>
                <div className="text-sm text-muted-foreground">Compatível com o modo local do SOG Desktop.</div>
              </div>

              {agente && (
                <div className="rounded-lg border border-border bg-muted/30 p-3 sm:col-span-2 xl:col-span-4">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Leitura do agente</div>
                  <div className="mt-1 font-medium text-foreground">{agente.mensagem || 'Sem mensagem operacional publicada.'}</div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    Última atualização: {formatarData(agente.atualizado_em)} · Relogin requerido: {agente.relogin_required ? 'Sim' : 'Não'}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardContent className="px-6 py-8 text-sm text-muted-foreground">
            Sem leitura disponível para a configuração operacional.
          </CardContent>
        </Card>
      )}
    </div>
  )
}
