import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { Sucumbente } from '../../types/processo'

interface Props {
  sucumbentes: Sucumbente[]
}

export default function SucumbentesTable({ sucumbentes }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sucumbentes</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">%</th>
                <th className="text-left py-2">Nome</th>
                <th className="text-left py-2">CPF/CNPJ</th>
                <th className="text-left py-2">Tipo</th>
              </tr>
            </thead>
            <tbody>
              {sucumbentes.map((s, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2">{s.percentual || s['% ou Fração'] || '-'}</td>
                  <td className="py-2">{s.nome || '-'}</td>
                  <td className="py-2">{s.cpf_cnpj || s.cpf || '-'}</td>
                  <td className="py-2">{s.tipo || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
