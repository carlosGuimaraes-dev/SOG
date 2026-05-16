import Alert, { AlertTitle, AlertDescription } from '../ui/Alert'

interface Props {
  areaDireito?: string
  suspensao?: boolean
  sucumbenteNome?: string
}

export default function AvisosAlert({ areaDireito, suspensao, sucumbenteNome }: Props) {
  const isDefaultArea = areaDireito === 'default'
  const hasWarning = isDefaultArea || suspensao || !sucumbenteNome

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
        </ul>
      </AlertDescription>
    </Alert>
  )
}
