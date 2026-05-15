import { useEffect, useState } from 'react'
import axios from 'axios'

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

  useEffect(() => {
    axios.get('/api/historico', { auth: { username: 'admin', password: 'admin' } })
      .then(res => setItems(res.data))
      .catch(() => alert('Erro ao carregar histórico'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Carregando...</p>

  return (
    <div>
      <h2>Histórico</h2>
      {items.length === 0 ? (
        <p>Nenhum registro no histórico.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#e9ecef' }}>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Número</th>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Polo Ativo</th>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Valor Total</th>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Status</th>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Data</th>
              <th style={{ border: '1px solid #ccc', padding: 8 }}>Obs</th>
            </tr>
          </thead>
          <tbody>
            {items.map(p => (
              <tr key={p.id}>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>{p.numero}</td>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>{p.polo_ativo || '-'}</td>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>{p.valor_total_recolher || '-'}</td>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: p.status === 'emitido' ? '#d4edda' : '#f8d7da',
                    color: p.status === 'emitido' ? '#155724' : '#721c24',
                  }}>
                    {p.status}
                  </span>
                </td>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>{new Date(p.atualizado_em).toLocaleString('pt-BR')}</td>
                <td style={{ border: '1px solid #ccc', padding: 8 }}>{p.obs_operador || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
