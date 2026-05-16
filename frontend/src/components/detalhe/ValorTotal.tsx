interface Props {
  valor?: string
}

export default function ValorTotal({ valor }: Props) {
  return (
    <div className="text-2xl font-bold text-success">
      Valor Total a Recolher: {valor || '-'}
    </div>
  )
}
