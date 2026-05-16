import { useEffect, useState } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import type { ProcessoCompleto } from '../types/processo'
import { useToast } from '../components/ToastProvider'

export function useProcesso(id: string | undefined) {
  const [data, setData] = useState<ProcessoCompleto | null>(null)
  const [loading, setLoading] = useState(true)
  const { addToast } = useToast()

  useEffect(() => {
    if (!id) {
      setLoading(false)
      return
    }
    api.get(ENDPOINTS.PROCESSOS + '/' + id)
      .then((res) => {
        setData(res.data)
      })
      .catch(() => addToast('Erro ao carregar detalhes', 'error'))
      .finally(() => setLoading(false))
  }, [id])

  return { data, loading }
}
