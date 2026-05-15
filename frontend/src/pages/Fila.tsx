import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

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

  async function fetchData() {
    try {
      const res = await axios.get('/api/processos', { auth: { username: 'admin', password: 'admin' } })
      setAguardando(res.data.aguardando_aprovacao || [])
      setManual(res.data.pendente_manual || [])
    } catch (e) {
      alert('Erro ao carregar processos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <p>Carregando...</p>

  return (
    <div>
      <h2>Aguardando Aprovação</h2>
      {aguardando.length === 0 ? (
        <p>Nenhum processo aguardando aprovação.</p>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {aguardando.map(p => (
            <div key={p.id} style={{ border: '1px solid #ccc', borderRadius: 8, padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{p.numero}</strong>
                <Link to={`/detalhe/${p.id}`} style={{ padding: '6px 12px', background: '#007bff', color: '#fff', borderRadius: 4, textDecoration: 'none' }}>
                  Revisar
                </Link>
              </div>
              <small style={{ color: '#666' }}>Criado em: {new Date(p.criado_em).toLocaleString('pt-BR')}</small>
            </div>
          ))}
        </div>
      )}

      <h2 style={{ marginTop: 32 }}>Pendente Manual (Área não mapeada)</h2>
      {manual.length === 0 ? (
        <p>Nenhum processo pendente manual.</p>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {manual.map(p => (
            <div key={p.id} style={{ border: '1px solid #f0ad4e', borderRadius: 8, padding: 16, background: '#fff3cd' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{p.numero}</strong>
                <Link to={`/detalhe/${p.id}`} style={{ padding: '6px 12px', background: '#f0ad4e', color: '#fff', borderRadius: 4, textDecoration: 'none' }}>
                  Revisar
                </Link>
              </div>
              <small style={{ color: '#856404' }}>Requer conferência manual dos Itens da Guia</small>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
