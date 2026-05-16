import { useEffect, useState } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'
import Badge from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import type { ProcessoHistorico } from '../types/processo'

export default function Historico() {
  const [items, setItems] = useState<ProcessoHistorico[]>([])
  const [loading, setLoading] = useState(true)
  const { addToast } = useToast()

  useEffect(() => {
    api.get(ENDPOINTS.HISTORICO)
      .then((res) => setItems(res.data))
      .catch(() => addToast('Erro ao carregar histórico', 'error'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Histórico</h2>

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Nenhum registro no histórico.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left py-3 px-4 font-medium">Número</th>
                    <th className="text-left py-3 px-4 font-medium">Polo Ativo</th>
                    <th className="text-left py-3 px-4 font-medium">Valor Total</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Data</th>
                    <th className="text-left py-3 px-4 font-medium">Obs</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((p) => (
                    <tr key={p.id} className="border-b last:border-0 hover:bg-muted/30">
                      <td className="py-3 px-4 font-medium">{p.numero}</td>
                      <td className="py-3 px-4">{p.polo_ativo || '-'}</td>
                      <td className="py-3 px-4">{p.valor_total_recolher || '-'}</td>
                      <td className="py-3 px-4">
                        <Badge variant={p.status === 'emitido' ? 'success' : 'destructive'}>
                          {p.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(p.atualizado_em).toLocaleString('pt-BR')}
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate">{p.obs_operador || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
