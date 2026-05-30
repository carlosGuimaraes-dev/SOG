import { useState, useCallback } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'

export function useReprocessar(id: string | undefined, onSuccess?: () => void) {
  const [actionLoading, setActionLoading] = useState(false)
  const { addToast } = useToast()

  const reprocessar = useCallback(
    async (motivo: string) => {
      if (!id) return
      if (!confirm('Solicitar reprocessamento no próximo ciclo?')) return
      setActionLoading(true)
      try {
        await api.post(ENDPOINTS.REPROCESSAR(id), { motivo })
        addToast('Reprocessamento solicitado para o próximo ciclo.', 'success')
        onSuccess?.()
      } catch {
        addToast('Erro ao solicitar reprocessamento', 'error')
      } finally {
        setActionLoading(false)
      }
    },
    [id, onSuccess]
  )

  return { reprocessar, actionLoading }
}
