import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'

export function useRejeitar(id: string | undefined) {
  const [actionLoading, setActionLoading] = useState(false)
  const navigate = useNavigate()
  const { addToast } = useToast()

  const rejeitar = useCallback(
    async (observacao: string) => {
      if (!id) return
      if (!confirm('Confirma rejeição?')) return
      setActionLoading(true)
      try {
        await api.post(ENDPOINTS.REJEITAR(id), { observacao })
        addToast('Processo rejeitado.', 'success')
        navigate('/')
      } catch {
        addToast('Erro ao rejeitar processo', 'error')
      } finally {
        setActionLoading(false)
      }
    },
    [id, navigate]
  )

  return { rejeitar, actionLoading }
}
