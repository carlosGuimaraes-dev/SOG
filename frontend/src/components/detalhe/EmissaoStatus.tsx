import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePollingStatus } from '../../hooks/usePollingStatus'
import { useToast } from '../../components/ToastProvider'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import Button from '../ui/Button'

interface Props {
  processoId: number | string
}

export default function EmissaoStatus({ processoId }: Props) {
  const { data } = usePollingStatus(String(processoId))
  const { addToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    if (!data) return
    const status = data.processo.status
    if (status === 'emitido') {
      addToast('Guia emitida com sucesso!', 'success')
    } else if (status === 'erro') {
      addToast('Falha na emissão da guia', 'error')
    }
  }, [data?.processo.status, addToast, data])

  const status = data?.processo.status
  const erroMsg = data?.processo.erro_msg

  if (status === 'emitido') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Status da Emissão</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-success font-semibold">✅ Emitido com sucesso</p>
          <Button variant="outline" onClick={() => navigate('/')} aria-label="Voltar para fila">
            Voltar para fila
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (status === 'erro') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Status da Emissão</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-destructive font-semibold">❌ Falha na emissão</p>
          {erroMsg && <p className="text-sm text-muted-foreground">{erroMsg}</p>}
          <Button variant="outline" onClick={() => navigate('/')} aria-label="Voltar para fila">
            Voltar para fila
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Status da Emissão</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"
            role="status"
            aria-label="Carregando"
          />
          <span className="text-sm">Emissão em andamento...</span>
        </div>
      </CardContent>
    </Card>
  )
}
