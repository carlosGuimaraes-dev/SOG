import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { OutroItem } from '../../types/processo'

interface Props {
  items: OutroItem[]
}

export default function OutrosItensTable({ items }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Outros Itens</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Item Guia</th>
                <th className="text-left py-2">Item Cálculo</th>
                <th className="text-left py-2">Qtd</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2">{item.item_guia || item.itemGuia || '-'}</td>
                  <td className="py-2">{item.item_calculo || item.itemCalculo || '-'}</td>
                  <td className="py-2">{item.quantidade || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
