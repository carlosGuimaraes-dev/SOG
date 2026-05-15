import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { useToast } from '../hooks/useToast'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { Card, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'

interface Processo {
  id: number
  numero: string
  status: string
  criado_em: string
}

export default function Fila() {
  const [aguardando, setAguardando] = useState<Processo[]>([])
  const [manual, setManual] = useState<Processo[]>([])
  const [loading, setLoading] = useState(true)
  const { toasts, addToast, removeToast } = useToast()

  async function fetchData() {
    try {
      const res = await api.get('/processos')
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

      <section>
        <h2 className="text-xl font-semibold mb-4">Aguardando Aprovação</h2>
        {aguardando.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Nenhum processo aguardando aprovação.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {aguardando.map((p) => (
              <Card key={p.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <div className="font-medium text-lg">{p.numero}</div>
                    <div className="text-sm text-muted-foreground">
                      Criado em: {new Date(p.criado_em).toLocaleString('pt-BR')}
                    </div>
                  </div>
                  <Link to={`/detalhe/${p.id}`}>
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
        {manual.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Nenhum processo pendente manual.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {manual.map((p) => (
              <Card key={p.id} className="border-warning/50 bg-warning/5">
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <div className="font-medium text-lg flex items-center gap-2">
                      {p.numero}
                      <Badge variant="warning">Manual</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Requer conferência manual dos Itens da Guia
                    </div>
                  </div>
                  <Link to={`/detalhe/${p.id}`}>
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
