import Alert, { AlertTitle, AlertDescription } from '../ui/Alert'

interface Props {
  mensagem: string
}

export default function ErroBanner({ mensagem }: Props) {
  return (
    <Alert variant="destructive" aria-live="assertive">
      <AlertTitle>Erro na execução</AlertTitle>
      <AlertDescription>{mensagem}</AlertDescription>
    </Alert>
  )
}
