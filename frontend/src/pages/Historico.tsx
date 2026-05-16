import { useEffect, useState, useMemo, useCallback } from 'react'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'
import Badge from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import Paginacao from '../components/historico/Paginacao'
import FiltrosHistorico, { type FiltrosState } from '../components/historico/FiltrosHistorico'
import BotaoExportar from '../components/historico/BotaoExportar'
import { parseValorMonetario } from '../lib/formatters'
import type { ProcessoHistorico } from '../types/processo'

const ITENS_POR_PAGINA = 20

export default function Historico() {
  const [items, setItems] = useState<ProcessoHistorico[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const [filtros, setFiltros] = useState<FiltrosState>({ status: 'todos', data: 'todos', valorMinimo: '' })
  const { addToast } = useToast()

  useEffect(() => {
    api.get(ENDPOINTS.HISTORICO)
      .then((res) => setItems(res.data))
      .catch(() => addToast('Erro ao carregar histórico', 'error'))
      .finally(() => setLoading(false))
  }, [addToast])

  const handleFiltrosChange = useCallback((novosFiltros: FiltrosState) => {
    setFiltros(novosFiltros)
    setPage(0)
  }, [])

  const itemsFiltrados = useMemo(() => {
    return items.filter((p) => {
      if (filtros.status !== 'todos' && p.status !== filtros.status) return false

      if (filtros.data !== 'todos') {
        const dias = parseInt(filtros.data, 10)
        const limite = new Date(Date.now() - dias * 24 * 60 * 60 * 1000)
        if (new Date(p.atualizado_em) < limite) return false
      }

      if (filtros.valorMinimo) {
        const min = parseFloat(filtros.valorMinimo)
        const valor = parseValorMonetario(p.valor_total_recolher)
        if (isNaN(min) || valor < min) return false
      }

      return true
    })
  }, [items, filtros])

  const paginatedItems = useMemo(() => {
    const start = page * ITENS_POR_PAGINA
    return itemsFiltrados.slice(start, start + ITENS_POR_PAGINA)
  }, [itemsFiltrados, page])

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
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Histórico</h2>
        <BotaoExportar />
      </div>

      <FiltrosHistorico onChange={handleFiltrosChange} />

      {itemsFiltrados.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {items.length === 0
              ? 'Nenhum registro no histórico.'
              : 'Nenhum registro corresponde aos filtros.'}
          </CardContent>
        </Card>
      ) : (
        <>
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
                    {paginatedItems.map((p) => (
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
          <Paginacao
            currentPage={page}
            totalItems={itemsFiltrados.length}
            itemsPerPage={ITENS_POR_PAGINA}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}
