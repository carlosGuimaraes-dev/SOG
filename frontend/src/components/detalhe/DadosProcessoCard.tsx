import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { DadosProcesso } from '../../types/processo'

interface Props {
  dados: DadosProcesso
}

export default function DadosProcessoCard({ dados: d }: Props) {
  const rows = [
    ['Instância', d.instancia],
    ['Circunscrição', d.circunscricao],
    ['Competência', d.competencia],
    ['Feito', d.feito],
    ['Classe', d.classe],
    ['Valor da Causa', d.valor_causa],
    ['Valor Atualizado', d.valor_causa_atualizado],
    ['Data Distribuição', d.data_distribuicao],
    ['Polo Ativo', d.polo_ativo],
    ['Polo Passivo', d.polo_passivo],
    ['Tipo Guia', d.tipo_guia],
    ['Pró-rata', d.pro_rata ? 'Sim' : 'Não'],
    ['Suspensão', d.suspensao_exigibilidade ? 'Sim' : 'Não'],
    ['Área', d.area_direito],
  ] as const

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dados do Processo</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-y-2">
          {rows.map(([label, val]) => (
            <div key={label} className="contents">
              <span className="text-muted-foreground">{label}</span>
              <span>{val || '-'}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
