import { useState, useCallback } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'

export function useAprovar(id: string | undefined) {
  const [actionLoading, setActionLoading] = useState(false)
  const { addToast } = useToast()

  const aprovar = useCallback(async () => {
    if (!id) return
    if (!confirm('Confirma aprovação?')) return
    setActionLoading(true)
    try {
      await api.post(ENDPOINTS.APROVAR(id))
      addToast('Aprovado! Emissão em andamento.', 'success')
    } catch {
      addToast('Erro ao aprovar processo', 'error')
    } finally {
      setActionLoading(false)
    }
  }, [id])

  return { aprovar, actionLoading }
}
