import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import Button from '../ui/Button'
import Textarea from '../ui/Textarea'

interface Props {
  observacao: string
  onObservacaoChange: (val: string) => void
  onAprovar: () => void
  onRejeitar: () => void
  onReprocessar: () => void
  actionLoading: boolean
  reprocessarLoading: boolean
  statusProcesso: string
  reprocessarSolicitadoEm?: string
}

export default function AcoesPanel({
  observacao,
  onObservacaoChange,
  onAprovar,
  onRejeitar,
  onReprocessar,
  actionLoading,
  reprocessarLoading,
  statusProcesso,
  reprocessarSolicitadoEm,
}: Props) {
  const podeReprocessar = ['erro', 'pendente_manual', 'rejeitado'].includes(statusProcesso)
  const reprocessarPendente = Boolean(reprocessarSolicitadoEm)

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
        {podeReprocessar && (
          <Button
            variant="outline"
            className="w-full"
            onClick={onReprocessar}
            disabled={actionLoading || reprocessarLoading || reprocessarPendente}
            aria-label="Reprocessar processo"
          >
            {reprocessarPendente
              ? 'Reprocessamento solicitado'
              : reprocessarLoading
                ? 'Solicitando...'
                : 'Reprocessar'}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
