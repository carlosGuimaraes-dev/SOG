import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { DadosProcesso } from '../../types/processo'

interface Props {
  dados: DadosProcesso
}

function contarPecas(valor?: string): number {
  if (!valor || valor.trim() === '') return 0
  return valor.split(',').length
}

export default function ResumoPreenchimento({ dados }: Props) {
  const totalPecas =
    contarPecas(dados.ids_oficios) +
    contarPecas(dados.ids_alvaras) +
    contarPecas(dados.ids_traslados) +
    contarPecas(dados.ids_mandados) +
    contarPecas(dados.ids_cartas_sentenca) +
    contarPecas(dados.ids_ar) +
    contarPecas(dados.ids_armp)

  const itensGuia = dados.outros_itens?.length ?? 0

  const resumoItems = [
    { label: 'Sucumbente', valor: dados.sucumbente_nome || 'Não identificado' },
    { label: 'Peças Marcadas', valor: totalPecas > 0 ? `${totalPecas} peças` : '-' },
    { label: 'Itens da Guia', valor: itensGuia > 0 ? `${itensGuia}` : 'Nenhum' },
    { label: 'Valor Total', valor: dados.valor_total_recolher || '-' },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resumo do Preenchimento Automático</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {resumoItems.map((item) => (
            <div key={item.label} className="flex flex-col">
              <span className="text-sm text-muted-foreground">{item.label}</span>
              <span className="text-lg font-semibold">{item.valor}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
