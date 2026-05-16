import Badge from '../ui/Badge'
import { parseValorMonetario } from '../../lib/formatters'
import type { Processo } from '../../types/processo'

interface PrioridadeBadgeProps {
  processo: Processo & { valor_total_recolher?: string }
}

export default function PrioridadeBadge({ processo }: PrioridadeBadgeProps) {
  const badges: { label: string; variant: 'destructive' | 'warning' | 'secondary' }[] = []

  if (processo.tentativas && processo.tentativas > 0 && processo.erro_msg) {
    badges.push({ label: 'Urgente', variant: 'destructive' })
  }

  if (processo.valor_total_recolher && parseValorMonetario(processo.valor_total_recolher) > 50000) {
    badges.push({ label: 'Alto Valor', variant: 'warning' })
  }

  const criadoEm = processo.criado_em ? new Date(processo.criado_em) : null
  if (criadoEm) {
    const diffMs = Date.now() - criadoEm.getTime()
    const diffDias = diffMs / (1000 * 60 * 60 * 24)
    if (diffDias > 7) {
      badges.push({ label: 'Antigo', variant: 'secondary' })
    }
  }

  return (
    <>
      {badges.map((b) => (
        <Badge key={b.label} variant={b.variant}>
          {b.label}
        </Badge>
      ))}
    </>
  )
}
