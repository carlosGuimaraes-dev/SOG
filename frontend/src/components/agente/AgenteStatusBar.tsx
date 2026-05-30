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
  | 'parando'
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

const STATUS_CONFIG: Record<string, StatusConfig> = {
  executando: { cor: 'bg-green-500', label: 'Executando' },
  dormindo: { cor: 'bg-green-400', label: 'Executando (pausa)' },
  autenticando: { cor: 'bg-blue-500', label: 'Autenticando' },
  aguardando_login: { cor: 'bg-yellow-500', label: 'Aguardando login' },
  parado: { cor: 'bg-gray-400', label: 'Parado' },
  desconhecido: { cor: 'bg-gray-300', label: 'Offline' },
  erro: { cor: 'bg-red-500', label: 'Erro' },
  iniciando: { cor: 'bg-blue-400', label: 'Iniciando' },
  parando: { cor: 'bg-orange-500', label: 'Parando' },
}

const INICIAR_HABILITADO: AgenteStatus[] = ['parado', 'desconhecido', 'erro']
const PARAR_HABILITADO: AgenteStatus[] = [
  'executando',
  'dormindo',
  'autenticando',
  'aguardando_login',
  'iniciando',
]

export default function AgenteStatusBar() {
  const [status, setStatus] = useState<AgenteStatus>('desconhecido')
  const [mensagem, setMensagem] = useState('')
  const [online, setOnline] = useState(false)
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
      const res = await api.get<{
        status: AgenteStatus
        mensagem: string
        online: boolean
      }>(ENDPOINTS.AGENTE_STATUS)
      setStatus(res.data.status)
      setMensagem(res.data.mensagem)
      setOnline(res.data.online)
    } catch {
      setStatus('desconhecido')
      setOnline(false)
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
      await api.post(ENDPOINTS.AGENTE_INICIAR)
      await fetchStatus()
    } catch {
      addToast('Erro ao enviar comando de iniciar', 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleParar() {
    setLoading(true)
    try {
      await api.post(ENDPOINTS.AGENTE_PARAR)
      await fetchStatus()
    } catch {
      addToast('Erro ao enviar comando de parar', 'error')
    } finally {
      setLoading(false)
    }
  }

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.desconhecido
  const podeIniciar = INICIAR_HABILITADO.includes(status)
  const podeParar = PARAR_HABILITADO.includes(status)

  return (
    <div
      className="flex flex-wrap items-center gap-4 p-3 bg-card border rounded-lg mb-6"
      role="region"
      aria-label="Status do agente de automação"
    >
      <div className="flex items-center gap-2">
        <span
          className={`w-3 h-3 rounded-full ${cfg.cor} ${online ? '' : 'opacity-40'}`}
          aria-hidden="true"
        />
        <span className="font-medium">{cfg.label}</span>
        {mensagem && (
          <span className="text-sm text-muted-foreground">— {mensagem}</span>
        )}
      </div>
      {ciclo && (
        <div className="text-sm text-muted-foreground">
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
          ▶ Iniciar Agente
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
