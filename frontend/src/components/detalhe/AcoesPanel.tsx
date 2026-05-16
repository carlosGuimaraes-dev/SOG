import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import Button from '../ui/Button'
import Textarea from '../ui/Textarea'

interface Props {
  observacao: string
  onObservacaoChange: (val: string) => void
  onAprovar: () => void
  onRejeitar: () => void
  actionLoading: boolean
}

export default function AcoesPanel({
  observacao,
  onObservacaoChange,
  onAprovar,
  onRejeitar,
  actionLoading,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Ações</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label htmlFor="obs-operador" className="text-sm font-medium">
            Observações do Operador
          </label>
          <Textarea
            id="obs-operador"
            value={observacao}
            onChange={(e) => onObservacaoChange(e.target.value)}
            aria-label="Observações do operador"
          />
        </div>
        <div className="flex gap-3">
          <Button
            className="flex-1 bg-success hover:bg-success/90"
            onClick={onAprovar}
            disabled={actionLoading}
            aria-label="Aprovar processo"
          >
            {actionLoading ? 'Processando...' : '✅ Aprovar'}
          </Button>
          <Button
            variant="destructive"
            className="flex-1"
            onClick={onRejeitar}
            disabled={actionLoading}
            aria-label="Rejeitar processo"
          >
            {actionLoading ? 'Processando...' : '❌ Rejeitar'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
