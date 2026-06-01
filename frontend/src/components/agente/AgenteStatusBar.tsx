import { useCallback, useEffect, useState } from 'react'
import api from '../../lib/api'
import { ENDPOINTS } from '../../lib/endpoints'
import { useToast } from '../ToastProvider'
import Button from '../ui/Button'

type AgenteStatus =
  | 'parado'
  | 'iniciando'
  | 'autenticando'
  | 'executando'
  | 'dormindo'
  | 'aguardando_login'
  | 'erro'
  | 'erro_pausado'
  | 'parando'
  | 'pausado'
  | 'interrompido'
  | 'desconhecido'

interface StatusConfig {
  cor: string
  label: string
}

interface CicloAgente {
  uuid: string
  rotulo: string
  status: string
  total_membros: number
  total_novos: number
  total_rearmados: number
  total_concluidos: number
  total_erros: number
}

interface AgenteStatusResponse {
  status: AgenteStatus
  mensagem: string
  online: boolean
  ciclo_uuid?: string | null
  pode_iniciar?: boolean
  pode_parar?: boolean
  relogin_required?: boolean
}

interface AgenteComandoResponse {
  message?: string
  resumed?: boolean
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  executando: { cor: 'bg-green-500', label: 'Executando' },
  dormindo: { cor: 'bg-green-400', label: 'Executando (pausa)' },
  autenticando: { cor: 'bg-blue-500', label: 'Autenticando' },
  aguardando_login: { cor: 'bg-yellow-500', label: 'Aguardando login' },
  pausado: { cor: 'bg-yellow-500', label: 'Pausado' },
  interrompido: { cor: 'bg-yellow-500', label: 'Interrompido' },
  parado: { cor: 'bg-gray-400', label: 'Parado' },
  desconhecido: { cor: 'bg-gray-300', label: 'Offline' },
  erro: { cor: 'bg-red-500', label: 'Erro' },
  erro_pausado: { cor: 'bg-red-500', label: 'Erro pausado' },
  iniciando: { cor: 'bg-blue-400', label: 'Iniciando' },
  parando: { cor: 'bg-orange-500', label: 'Parando' },
}

const ESTADOS_CICLO_ATIVO: AgenteStatus[] = [
  'iniciando',
  'autenticando',
  'executando',
  'dormindo',
  'parando',
]
const ESTADOS_CICLO_RETOMAVEL: AgenteStatus[] = [
  'pausado',
  'interrompido',
  'erro_pausado',
  'erro',
  'aguardando_login',
]
const INICIAR_HABILITADO: AgenteStatus[] = [
  'parado',
  'desconhecido',
  'erro',
  'erro_pausado',
  'pausado',
  'interrompido',
  'aguardando_login',
]
const PARAR_HABILITADO: AgenteStatus[] = [
  'executando',
  'dormindo',
  'autenticando',
  'aguardando_login',
  'iniciando',
]

function normalizarMensagemAgente(mensagem: string): string {
  if (!mensagem) return ''
  const erroBrowser =
    mensagem.includes('BrowserType.launch') ||
    mensagem.includes('Target page, context or browser has been closed') ||
    mensagem.includes('chrome_crashpad_handler') ||
    mensagem.includes('Connection reset by peer')

  if (erroBrowser) {
    return 'Não foi possível abrir o navegador do agente para login. O SOG tenta abrir PJe e SISTJWEB automaticamente, mas o Chromium fechou ao iniciar neste ambiente. Verifique o suporte gráfico do Docker/Playwright e reinicie o agente.'
  }

  return mensagem.length > 280 ? `${mensagem.slice(0, 280)}...` : mensagem
}

export default function AgenteStatusBar() {
  const [status, setStatus] = useState<AgenteStatus>('desconhecido')
  const [mensagem, setMensagem] = useState('')
  const [online, setOnline] = useState(false)
  const [cicloUuid, setCicloUuid] = useState<string | null>(null)
  const [podeIniciarApi, setPodeIniciarApi] = useState(true)
  const [podePararApi, setPodePararApi] = useState(false)
  const [reloginRequired, setReloginRequired] = useState(false)
  const [ciclo, setCiclo] = useState<CicloAgente | null>(null)
  const [loading, setLoading] = useState(false)
  const { addToast } = useToast()

  const fetchCiclo = useCallback(async () => {
    try {
      const atual = await api.get<CicloAgente | null>(ENDPOINTS.AGENTE_CICLO_ATUAL)
      if (atual.data) {
        setCiclo(atual.data)
        return
      }
      const ultimo = await api.get<CicloAgente | null>(ENDPOINTS.AGENTE_ULTIMO_CICLO)
      setCiclo(ultimo.data)
    } catch {
      setCiclo(null)
    }
  }, [])

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get<AgenteStatusResponse>(ENDPOINTS.AGENTE_STATUS)
      setStatus(res.data.status)
      setMensagem(normalizarMensagemAgente(res.data.mensagem))
      setOnline(res.data.online)
      setCicloUuid(res.data.ciclo_uuid ?? null)
      setPodeIniciarApi(res.data.pode_iniciar ?? true)
      setPodePararApi(res.data.pode_parar ?? false)
      setReloginRequired(res.data.relogin_required ?? false)
    } catch {
      setStatus('desconhecido')
      setOnline(false)
      setCicloUuid(null)
      setPodeIniciarApi(true)
      setPodePararApi(false)
      setReloginRequired(false)
    }
    await fetchCiclo()
  }, [fetchCiclo])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  async function handleIniciar() {
    setLoading(true)
    try {
      const res = await api.post<AgenteComandoResponse>(ENDPOINTS.AGENTE_INICIAR)
      if (res.data.message) {
        addToast(res.data.message, res.data.resumed ? 'info' : 'success')
      }
      await fetchStatus()
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      addToast(detail || 'Erro ao enviar comando de iniciar', 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleParar() {
    setLoading(true)
    try {
      const res = await api.post<AgenteComandoResponse>(ENDPOINTS.AGENTE_PARAR)
      if (res.data.message) {
        addToast(res.data.message, 'info')
      }
      await fetchStatus()
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      addToast(detail || 'Erro ao enviar comando de parar', 'error')
    } finally {
      setLoading(false)
    }
  }

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.desconhecido
  const podeIniciar = podeIniciarApi && INICIAR_HABILITADO.includes(status)
  const podeParar = podePararApi && PARAR_HABILITADO.includes(status)
  const cicloAtivo = ESTADOS_CICLO_ATIVO.includes(status)
  const cicloRetomavel = Boolean(cicloUuid) && ESTADOS_CICLO_RETOMAVEL.includes(status)
  const acaoPrimariaLabel = reloginRequired || status === 'aguardando_login'
    ? '▶ Retomar após login'
    : cicloRetomavel
      ? '▶ Retomar ciclo'
      : '▶ Iniciar novo ciclo'
  const cicloBadge = reloginRequired || status === 'aguardando_login'
    ? {
        className: 'bg-yellow-100 text-yellow-900',
        label: 'Relogin pendente',
      }
    : cicloAtivo
      ? {
          className: 'bg-green-100 text-green-800',
          label: 'Ciclo ativo',
        }
      : cicloRetomavel
        ? {
            className: 'bg-amber-100 text-amber-900',
            label: 'Ciclo pausado',
          }
        : null

  return (
    <div
      className="flex flex-wrap items-center gap-4 p-3 bg-card border rounded-lg mb-6"
      role="region"
      aria-label="Status do agente de automação"
    >
      <div className="flex min-w-0 items-center gap-2">
        <span
          className={`w-3 h-3 rounded-full ${cfg.cor} ${online ? '' : 'opacity-40'}`}
          aria-hidden="true"
        />
        <span className="font-medium">{cfg.label}</span>
        {mensagem && (
          <span className="min-w-0 break-words text-sm text-muted-foreground">— {mensagem}</span>
        )}
        {reloginRequired && (
          <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-900">
            Relogin necessário
          </span>
        )}
      </div>
      {ciclo && (
        <div className="text-sm text-muted-foreground">
          {cicloBadge && (
            <span className={`mr-2 rounded px-2 py-0.5 text-xs font-medium ${cicloBadge.className}`}>
              {cicloBadge.label}
            </span>
          )}
          <span className="font-medium text-foreground">{ciclo.rotulo}</span>
          <span>
            {' '}
            · {ciclo.total_membros} no lote · {ciclo.total_novos} novos ·{' '}
            {ciclo.total_rearmados} rearmados · {ciclo.total_concluidos} concluídos
            {ciclo.total_erros > 0 ? ` · ${ciclo.total_erros} erros` : ''}
          </span>
        </div>
      )}
      <div className="ml-auto flex gap-2">
        <Button
          onClick={handleIniciar}
          disabled={!podeIniciar || loading}
          aria-label="Iniciar agente de automação"
        >
          {acaoPrimariaLabel}
        </Button>
        <Button
          onClick={handleParar}
          disabled={!podeParar || loading}
          variant="outline"
          aria-label="Parar agente de automação"
        >
          ⏹ Parar Agente
        </Button>
      </div>
    </div>
  )
}
