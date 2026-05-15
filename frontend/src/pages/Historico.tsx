import { useEffect, useState } from 'react'
import api from '../lib/api'
import { useToast } from '../hooks/useToast'
import Badge from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'

interface Processo {
  id: number
  numero: string
  polo_ativo: string
  valor_total_recolher: string
  status: string
  atualizado_em: string
  obs_operador: string
}

export default function Historico() {
  const [items, setItems] = useState<Processo[]>([])
  const [loading, setLoading] = useState(true)
  const { toasts, addToast, removeToast } = useToast()

  useEffect(() => {
    api.get('/historico')
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
      {/* Toasts */}
      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
          {toasts.map((t) => (
            <div
              key={t.id}
              className={`rounded-lg px-4 py-3 text-sm shadow-lg cursor-pointer ${
                t.type === 'error' ? 'bg-destructive text-destructive-foreground' : t.type === 'success' ? 'bg-success text-success-foreground' : 'bg-primary text-primary-foreground'
              }`}
              onClick={() => removeToast(t.id)}
            >
              {t.message}
            </div>
          ))}
        </div>
      )}

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
