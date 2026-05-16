import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { Compensacao } from '../../types/processo'

interface Props {
  items?: Compensacao[]
}

export default function CompensacaoTable({ items }: Props) {
  if (!items || items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Compensação</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Nenhuma compensação</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Compensação</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Data</th>
                <th className="text-left py-2">Valor</th>
                <th className="text-left py-2">Guia de Origem</th>
              </tr>
            </thead>
            <tbody>
              {items.map((c, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2">{c.data || '-'}</td>
                  <td className="py-2">{c.valor || '-'}</td>
                  <td className="py-2">{c.numero_guia || c.numeroGuia || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
