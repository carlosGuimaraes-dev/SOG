import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'

export function useAprovar(id: string | undefined) {
  const [actionLoading, setActionLoading] = useState(false)
  const navigate = useNavigate()
  const { addToast } = useToast()

  const aprovar = useCallback(async () => {
    if (!id) return
    if (!confirm('Confirma aprovação?')) return
    setActionLoading(true)
    try {
      await api.post(ENDPOINTS.APROVAR(id))
      addToast('Aprovado! Emissão em andamento.', 'success')
      navigate('/')
    } catch {
      addToast('Erro ao aprovar processo', 'error')
    } finally {
      setActionLoading(false)
    }
  }, [id, navigate])

  return { aprovar, actionLoading }
}
