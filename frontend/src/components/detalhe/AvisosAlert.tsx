import Alert, { AlertTitle, AlertDescription } from '../ui/Alert'
import { parseValorMonetario } from '../../lib/formatters'

interface Props {
  areaDireito?: string
  suspensao?: boolean
  sucumbenteNome?: string
  valorTotalRecolher?: string
}

export default function AvisosAlert({ areaDireito, suspensao, sucumbenteNome, valorTotalRecolher }: Props) {
  const isDefaultArea = areaDireito === 'default'
  const valorAlto = parseValorMonetario(valorTotalRecolher) > 50000
  const hasWarning = isDefaultArea || suspensao || !sucumbenteNome || valorAlto

  if (!hasWarning) return null

  return (
    <Alert variant={isDefaultArea ? 'warning' : 'default'}>
      <AlertTitle>Avisos</AlertTitle>
      <AlertDescription>
        <ul className="list-disc pl-4 space-y-1 mt-1">
          {isDefaultArea && (
            <li>Área não mapeada — verifique Outros Itens manualmente</li>
          )}
          {suspensao && (
            <li>Suspensão de exigibilidade detectada — confirmar isenção</li>
          )}
          {!sucumbenteNome && (
            <li>Sucumbente não identificado na sentença</li>
          )}
          {valorAlto && (
            <li>Valor total muito alto (acima de R$ 50.000) — confira manualmente</li>
          )}
        </ul>
      </AlertDescription>
    </Alert>
  )
}
