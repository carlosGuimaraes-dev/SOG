import { useState } from 'react'
import Button from '../ui/Button'
import { ENDPOINTS } from '../../lib/endpoints'
import api from '../../lib/api'
import { useToast } from '../../hooks/useToast'

export default function BotaoExportar() {
  const [isLoading, setIsLoading] = useState(false)
  const { addToast } = useToast()

  async function handleClick() {
    setIsLoading(true)
    try {
      const response = await api.get(ENDPOINTS.HISTORICO_EXPORTAR, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'historico.csv'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      addToast('Erro ao exportar histórico', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      variant="outline"
      onClick={handleClick}
      disabled={isLoading}
      aria-label="Exportar histórico em CSV"
    >
      {isLoading ? '⏳ Exportando...' : '📥 Exportar CSV'}
    </Button>
  )
}
