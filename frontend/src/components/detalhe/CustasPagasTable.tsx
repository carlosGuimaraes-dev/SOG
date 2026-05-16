import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { CustasPaga } from '../../types/processo'

interface Props {
  items: CustasPaga[]
}

export default function CustasPagasTable({ items }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Custas Pagas</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Data</th>
                <th className="text-left py-2">Valor</th>
                <th className="text-left py-2">Guia</th>
              </tr>
            </thead>
            <tbody>
              {items.map((cp, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2">{cp.data || '-'}</td>
                  <td className="py-2">{cp.valor || '-'}</td>
                  <td className="py-2">{cp.numero_guia || cp.numeroGuia || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
