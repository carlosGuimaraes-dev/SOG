import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useToast } from '../hooks/useToast'
import Button from '../components/ui/Button'
// import Badge from '../components/ui/Badge'
import Alert, { AlertTitle, AlertDescription } from '../components/ui/Alert'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'

export default function Detalhe() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<any>(null)
  const [obs, setObs] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const { toasts, addToast, removeToast } = useToast()

  useEffect(() => {
    api.get(`/processos/${id}`)
      .then((res) => {
        setData(res.data)
        setObs(res.data.dados?.obs_operador || '')
      })
      .catch(() => addToast('Erro ao carregar detalhes', 'error'))
      .finally(() => setLoading(false))
  }, [id])

  async function aprovar() {
    if (!confirm('Confirma aprovação?')) return
    setActionLoading(true)
    try {
      await api.post(`/aprovar/${id}`)
      addToast('Aprovado! Emissão em andamento.', 'success')
      navigate('/')
    } catch {
      addToast('Erro ao aprovar processo', 'error')
    } finally {
      setActionLoading(false)
    }
  }

  async function rejeitar() {
    if (!confirm('Confirma rejeição?')) return
    setActionLoading(true)
    try {
      await api.post(`/rejeitar/${id}`, { observacao: obs })
      addToast('Processo rejeitado.', 'success')
      navigate('/')
    } catch {
      addToast('Erro ao rejeitar processo', 'error')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading || !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const p = data.processo
  const d = data.dados || {}

  return (
    <div className="space-y-4">
      {/* Toasts */}
      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
          {toasts.map((t) => (
            <div
              key={t.id}
              className={`rounded-lg px-4 py-3 text-sm text-white shadow-lg cursor-pointer ${
                t.type === 'error' ? 'bg-destructive' : t.type === 'success' ? 'bg-success' : 'bg-primary'
              }`}
              onClick={() => removeToast(t.id)}
            >
              {t.message}
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Processo {p.numero}</h2>
        <Button variant="outline" onClick={() => navigate('/')}>
          ← Voltar
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Dados do Processo</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-y-2">
                <span className="text-muted-foreground">Instância</span>
                <span>{d.instancia || '-'}</span>
                <span className="text-muted-foreground">Circunscrição</span>
                <span>{d.circunscricao || '-'}</span>
                <span className="text-muted-foreground">Competência</span>
                <span>{d.competencia || '-'}</span>
                <span className="text-muted-foreground">Feito</span>
                <span>{d.feito || '-'}</span>
                <span className="text-muted-foreground">Classe</span>
                <span>{d.classe || '-'}</span>
                <span className="text-muted-foreground">Valor da Causa</span>
                <span>{d.valor_causa || '-'}</span>
                <span className="text-muted-foreground">Valor Atualizado</span>
                <span>{d.valor_causa_atualizado || '-'}</span>
                <span className="text-muted-foreground">Data Distribuição</span>
                <span>{d.data_distribuicao || '-'}</span>
                <span className="text-muted-foreground">Polo Ativo</span>
                <span>{d.polo_ativo || '-'}</span>
                <span className="text-muted-foreground">Polo Passivo</span>
                <span>{d.polo_passivo || '-'}</span>
                <span className="text-muted-foreground">Tipo Guia</span>
                <span>{d.tipo_guia || '-'}</span>
                <span className="text-muted-foreground">Pró-rata</span>
                <span>{d.pro_rata ? 'Sim' : 'Não'}</span>
                <span className="text-muted-foreground">Suspensão</span>
                <span>{d.suspensao_exigibilidade ? 'Sim' : 'Não'}</span>
                <span className="text-muted-foreground">Área</span>
                <span>{d.area_direito || '-'}</span>
              </div>
            </CardContent>
          </Card>

          {d.sucumbentes && Array.isArray(d.sucumbentes) && d.sucumbentes.length > 0 && (
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
                      {d.sucumbentes.map((s: any, i: number) => (
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
          )}

          <Card>
            <CardHeader>
              <CardTitle>Peças Processuais (IDs PJE)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 text-sm">
              {[
                ['Ofícios', d.ids_oficios],
                ['Alvarás', d.ids_alvaras],
                ['Traslados', d.ids_traslados],
                ['Mandados', d.ids_mandados],
                ['Cartas de Sentença', d.ids_cartas_sentenca],
                ['AR', d.ids_ar],
                ['AR/MP', d.ids_armp],
              ].map(([label, val]) => (
                <div key={label} className="flex justify-between">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-mono">{val || '-'}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {d.outros_itens && Array.isArray(d.outros_itens) && d.outros_itens.length > 0 && (
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
                      {d.outros_itens.map((item: any, i: number) => (
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
          )}

          {d.custas_pagas && Array.isArray(d.custas_pagas) && d.custas_pagas.length > 0 && (
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
                      {d.custas_pagas.map((cp: any, i: number) => (
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
          )}

          <div className="text-2xl font-bold text-success">
            Valor Total a Recolher: {d.valor_total_recolher || '-'}
          </div>
        </div>

        <div className="space-y-6">
          {d.screenshot_path && (
            <Card>
              <CardHeader>
                <CardTitle>Screenshot SISTJWEB</CardTitle>
              </CardHeader>
              <CardContent>
                <img
                  src={`/screenshots/${p.numero}_sistjweb.png`}
                  alt="Screenshot"
                  className="w-full rounded-lg border"
                />
              </CardContent>
            </Card>
          )}

          {(d.area_direito === 'default' || d.suspensao_exigibilidade || !d.sucumbente_nome) && (
            <Alert variant={d.area_direito === 'default' ? 'warning' : 'default'}>
              <AlertTitle>Avisos</AlertTitle>
              <AlertDescription>
                <ul className="list-disc pl-4 space-y-1 mt-1">
                  {d.area_direito === 'default' && (
                    <li>Área não mapeada — verifique Outros Itens manualmente</li>
                  )}
                  {d.suspensao_exigibilidade && (
                    <li>Suspensão de exigibilidade detectada — confirmar isenção</li>
                  )}
                  {!d.sucumbente_nome && (
                    <li>Sucumbente não identificado na sentença</li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Ações</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Observações do Operador</label>
                <textarea
                  value={obs}
                  onChange={(e) => setObs(e.target.value)}
                  rows={4}
                  className="mt-1 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  className="flex-1 bg-success hover:bg-success/90"
                  onClick={aprovar}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processando...' : '✅ Aprovar'}
                </Button>
                <Button
                  variant="destructive"
                  className="flex-1"
                  onClick={rejeitar}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processando...' : '❌ Rejeitar'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
