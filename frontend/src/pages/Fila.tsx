import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { ENDPOINTS } from '../lib/endpoints'
import { useToast } from '../components/ToastProvider'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import AgenteStatusBar from '../components/agente/AgenteStatusBar'
import BuscaProcesso from '../components/fila/BuscaProcesso'
import PrioridadeBadge from '../components/fila/PrioridadeBadge'
import type { Processo } from '../types/processo'

function normalizarNumero(n: string): string {
  return n.replace(/\D/g, '')
}

function filtrarProcessos(processos: Processo[], busca: string): Processo[] {
  if (!busca.trim()) return processos
  const termo = normalizarNumero(busca)
  return processos.filter((p) => normalizarNumero(p.numero).includes(termo))
}

export default function Fila() {
  const [aguardando, setAguardando] = useState<Processo[]>([])
  const [manual, setManual] = useState<Processo[]>([])
  const [loading, setLoading] = useState(true)
  const [busca, setBusca] = useState('')
  const { addToast } = useToast()

  async function fetchData() {
    try {
      const res = await api.get(ENDPOINTS.PROCESSOS)
      setAguardando(res.data.aguardando_aprovacao || [])
      setManual(res.data.pendente_manual || [])
    } catch {
      addToast('Erro ao carregar processos', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const aguardandoFiltrado = useMemo(() => filtrarProcessos(aguardando, busca), [aguardando, busca])
  const manualFiltrado = useMemo(() => filtrarProcessos(manual, busca), [manual, busca])
  const nenhumResultado = busca.trim() !== '' && aguardandoFiltrado.length === 0 && manualFiltrado.length === 0

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <AgenteStatusBar />
      <BuscaProcesso valor={busca} onChange={setBusca} />

      {nenhumResultado && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Nenhum processo encontrado para esta busca.
          </CardContent>
        </Card>
      )}

      <section>
        <h2 className="text-xl font-semibold mb-4">Aguardando Aprovação</h2>
        {aguardandoFiltrado.length === 0 ? (
          !nenhumResultado && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Nenhum processo aguardando aprovação.
              </CardContent>
            </Card>
          )
        ) : (
          <div className="grid gap-4">
            {aguardandoFiltrado.map((p) => (
              <Card key={p.id} className={p.erro_msg ? 'border-destructive/50 bg-destructive/5' : ''}>
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <div className="font-medium text-lg flex items-center gap-2">
                      {p.numero}
                      <PrioridadeBadge processo={p} />
                      {p.erro_msg && <Badge variant="destructive">Erro</Badge>}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Criado em: {new Date(p.criado_em).toLocaleString('pt-BR')}
                    </div>
                    {p.tentativas !== undefined && p.tentativas > 0 && (
                      <div className="text-sm text-muted-foreground">
                        Tentativas: {p.tentativas}
                      </div>
                    )}
                  </div>
                  <Link to={`/detalhe/${p.id}`} aria-label={`Revisar processo ${p.numero}`}>
                    <Button>Revisar</Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Pendente Manual</h2>
        {manualFiltrado.length === 0 ? (
          !nenhumResultado && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Nenhum processo pendente manual.
              </CardContent>
            </Card>
          )
        ) : (
          <div className="grid gap-4">
            {manualFiltrado.map((p) => (
              <Card
                key={p.id}
                className={
                  p.erro_msg
                    ? 'border-destructive/50 bg-destructive/5'
                    : 'border-warning/50 bg-warning/5'
                }
              >
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <div className="font-medium text-lg flex items-center gap-2">
                      {p.numero}
                      <Badge variant="warning">Manual</Badge>
                      <PrioridadeBadge processo={p} />
                      {p.erro_msg && <Badge variant="destructive">Erro</Badge>}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Requer conferência manual dos Itens da Guia
                    </div>
                    {p.tentativas !== undefined && p.tentativas > 0 && (
                      <div className="text-sm text-muted-foreground">
                        Tentativas: {p.tentativas}
                      </div>
                    )}
                  </div>
                  <Link to={`/detalhe/${p.id}`} aria-label={`Revisar processo ${p.numero}`}>
                    <Button variant="outline">Revisar</Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
