import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { Documento } from '../../types/processo'

interface Props {
  documentos?: Documento[]
}

export default function DocumentosPje({ documentos }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Documentos PJE</CardTitle>
      </CardHeader>
      <CardContent>
        {(!documentos || documentos.length === 0) ? (
          <p className="text-sm text-muted-foreground">Nenhum documento extraído</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Tipo</th>
                  <th className="text-left py-2">Data de Assinatura</th>
                  <th className="text-left py-2">Nome</th>
                </tr>
              </thead>
              <tbody>
                {documentos.map((doc) => (
                  <tr key={doc.id} className="border-b last:border-0">
                    <td className="py-2">{doc.tipo}</td>
                    <td className="py-2">
                      {doc.data_assinatura
                        ? new Date(doc.data_assinatura).toLocaleDateString('pt-BR')
                        : '-'}
                    </td>
                    <td className="py-2">{doc.nome || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
