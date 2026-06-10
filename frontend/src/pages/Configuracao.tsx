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
const SOG_SESSION_BROWSER_URL = 'http://127.0.0.1:47831/sog/session-browser/open'
const PASSOS_AUTENTICACAO = ['Entre no PJe.', 'Entre no SISTJWEB.', 'Aguarde validação automática.']

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

function variantBadgeSessao(status: SessaoDashboard): 'success' | 'warning' | 'destructive' {
  if (status.logado) return 'success'
  if (/falha/i.test(status.mensagem)) return 'destructive'
  return 'warning'
}

function resumoSessao(status: SessaoDashboard): string {
  if (status.logado) return 'Sessão ativa'
  if (/falha/i.test(status.mensagem)) return 'Falha na validação'
  return 'Aguardando login'
}

function mensagemPrincipal(dashboard: DashboardSessoesResponse | null) {
  if (!dashboard) {
    return {
      titulo: 'Aguardando leitura da autenticação assistida.',
      descricao: 'Abra o Navegador de sessão do SOG para iniciar o login do PJe e do SISTJWEB.',
      variant: 'default' as const,
    }
  }

  if (dashboard.pje.logado && dashboard.sistj.logado) {
    return {
      titulo: 'Sistemas conectados. O agente pode continuar.',
      descricao: 'PJe e SISTJWEB estão ativos na mesma sessão do Navegador de sessão do SOG.',
      variant: 'default' as const,
    }
  }

  if (dashboard.pje.logado || dashboard.sistj.logado) {
    return {
      titulo: 'Falta concluir o login no sistema pendente.',
      descricao: dashboard.pje.logado
        ? 'SISTJWEB ainda precisa ser validado no Navegador de sessão do SOG.'
        : 'PJe ainda precisa ser validado no Navegador de sessão do SOG.',
      variant: 'warning' as const,
    }
  }

  return {
    titulo: 'Aguardando login no navegador do SOG.',
    descricao: 'Entre no PJe e no SISTJWEB no Navegador de sessão do SOG. A validação continua automaticamente.',
    variant: 'default' as const,
  }
}

function StatusSessaoCard({
  titulo,
  descricao,
  status,
  destacarPendente,
}: {
  titulo: string
  descricao: string
  status: SessaoDashboard
  destacarPendente: boolean
}) {
  const ativo = status.logado

  return (
    <Card className={destacarPendente ? 'border-warning/50 shadow-sm shadow-warning/20' : undefined}>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <CardTitle>{titulo}</CardTitle>
            <p className="text-sm text-muted-foreground">{descricao}</p>
          </div>
          <Badge variant={variantBadgeSessao(status)}>{resumoSessao(status)}</Badge>
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
        {destacarPendente && (
          <p className="text-sm font-medium text-warning-foreground">
            Falta concluir o login do {titulo} no Navegador de sessão do SOG.
          </p>
        )}
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
  const [openingSessionBrowser, setOpeningSessionBrowser] = useState(false)

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

  useEffect(() => {
    if (!dashboard || (dashboard.pje.logado && dashboard.sistj.logado)) {
      return undefined
    }

    const intervalId = window.setInterval(() => {
      void carregar()
    }, 5000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [carregar, dashboard])

  function abrirSistema(url: string, nome: string) {
    window.open(url, '_blank', 'noopener,noreferrer')
    addToast(`${nome} aberto em nova aba do navegador local.`, 'info')
  }

  async function abrirNavegadorDeSessao() {
    setOpeningSessionBrowser(true)
    try {
      const response = await fetch(SOG_SESSION_BROWSER_URL, {
        method: 'POST',
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok || payload?.ok === false) {
        throw new Error(payload?.message || 'Não foi possível abrir o Navegador de sessão do SOG.')
      }
      addToast(payload?.message || 'Navegador de sessão do SOG aberto com sucesso.', 'success')
    } catch (err: any) {
      addToast(
        err?.message || 'Não foi possível abrir o Navegador de sessão do SOG. Abra o SOG Desktop e tente novamente.',
        'error',
      )
    } finally {
      setOpeningSessionBrowser(false)
    }
  }

  const resumoAutenticacao = mensagemPrincipal(dashboard)
  const sistemaPendenteUnico = dashboard
    ? dashboard.pje.logado === dashboard.sistj.logado
      ? null
      : dashboard.pje.logado
        ? 'SISTJWEB'
        : 'PJe'
    : null

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Configuração operacional</h2>
        <p className="text-sm text-muted-foreground">
          Conecte PJe e SISTJWEB no Navegador de sessão do SOG e acompanhe a leitura operacional sem sair do dashboard.
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

      <Card>
        <CardHeader>
          <CardTitle>Conexão com sistemas externos</CardTitle>
          <p className="text-sm text-muted-foreground">
            Conecte PJe e SISTJWEB no navegador de sessão do SOG. O agente reutiliza essa mesma sessão para operar.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1 text-sm text-muted-foreground">
              <p>Use este fluxo principal quando precisar autenticar os sistemas externos para o agente.</p>
              <p>Abra sites externamente apenas para revisão manual fora da operação assistida.</p>
            </div>
            <Button type="button" onClick={abrirNavegadorDeSessao} disabled={openingSessionBrowser}>
              {openingSessionBrowser ? 'Abrindo navegador de sessão...' : 'Conectar PJe e SISTJWEB'}
            </Button>
          </div>

          <Alert variant={resumoAutenticacao.variant} aria-live="polite">
            <AlertTitle>{resumoAutenticacao.titulo}</AlertTitle>
            <AlertDescription>{resumoAutenticacao.descricao}</AlertDescription>
          </Alert>

          <div className="rounded-lg border border-border bg-muted/20 p-4">
            <p className="text-sm font-medium text-foreground">Passo a passo</p>
            <ol className="mt-3 space-y-2 text-sm text-muted-foreground">
              {PASSOS_AUTENTICACAO.map((passo, index) => (
                <li key={passo} className="flex items-start gap-3">
                  <span className="mt-0.5 inline-flex h-5 w-5 flex-none items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {index + 1}
                  </span>
                  <span>{passo}</span>
                </li>
              ))}
            </ol>
          </div>
        </CardContent>
      </Card>

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
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Status da autenticação assistida</CardTitle>
              <p className="text-sm text-muted-foreground">
                Acompanhe a leitura independente de PJe e SISTJWEB enquanto o SOG valida a sessão do navegador.
              </p>
            </CardHeader>
            <CardContent className="grid gap-4 lg:grid-cols-2">
              <StatusSessaoCard
                titulo="PJe"
                descricao="Sessão de login do tribunal usada pelo agente." 
                status={dashboard.pje}
                destacarPendente={sistemaPendenteUnico === 'PJe'}
              />
              <StatusSessaoCard
                titulo="SISTJWEB"
                descricao="Sessão externa necessária para preenchimento e emissão." 
                status={dashboard.sistj}
                destacarPendente={sistemaPendenteUnico === 'SISTJWEB'}
              />
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Abrir site externamente</CardTitle>
              <p className="text-sm text-muted-foreground">
                Use estas ações apenas para revisão manual fora do fluxo principal de autenticação assistida do agente.
              </p>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 sm:flex-row">
              <Button type="button" variant="outline" onClick={() => abrirSistema(PJE_URL, 'PJe')}>
                Abrir PJe externamente
              </Button>
              <Button type="button" variant="outline" onClick={() => abrirSistema(SISTJWEB_URL, 'SISTJWEB')}>
                Abrir SISTJWEB externamente
              </Button>
            </CardContent>
          </Card>

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
