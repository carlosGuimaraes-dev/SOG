import { useEffect, useRef, useState, useCallback } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import type { ProcessoCompleto } from '../types/processo'

interface UsePollingStatusReturn {
  data: ProcessoCompleto | null
  loading: boolean
  error: string | null
  stop: () => void
}

export function usePollingStatus(
  id: string | undefined,
  intervaloMs = 5000
): UsePollingStatusReturn {
  const [data, setData] = useState<ProcessoCompleto | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!id) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    const fetchStatus = async () => {
      try {
        const res = await api.get<ProcessoCompleto>(ENDPOINTS.PROCESSOS + '/' + id)
        setData(res.data)
        if (res.data.processo.status !== 'aprovado') {
          stop()
        }
      } catch {
        setError('Erro ao consultar status da emissão')
        stop()
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()

    intervalRef.current = setInterval(fetchStatus, intervaloMs)

    return () => {
      stop()
    }
  }, [id, intervaloMs, stop])

  return { data, loading, error, stop }
}
