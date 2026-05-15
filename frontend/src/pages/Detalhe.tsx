import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function Detalhe() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<any>(null)
  const [obs, setObs] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/processos/${id}`, { auth: { username: 'admin', password: 'admin' } })
      .then(res => {
        setData(res.data)
        setObs(res.data.dados?.obs_operador || '')
      })
      .catch(() => alert('Erro ao carregar detalhes'))
      .finally(() => setLoading(false))
  }, [id])

  async function aprovar() {
    if (!confirm('Confirma aprovação?')) return
    await axios.post(`/api/aprovar/${id}`, {}, { auth: { username: 'admin', password: 'admin' } })
    alert('Aprovado! Emissão em andamento.')
    navigate('/')
  }

  async function rejeitar() {
    if (!confirm('Confirma rejeição?')) return
    await axios.post(`/api/rejeitar/${id}`, { observacao: obs }, { auth: { username: 'admin', password: 'admin' } })
    alert('Rejeitado.')
    navigate('/')
  }

  if (loading || !data) return <p>Carregando...</p>

  const p = data.processo
  const d = data.dados || {}

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
      <div>
        <h2>Processo {p.numero}</h2>
        <div style={{ background: '#f8f9fa', padding: 16, borderRadius: 8, marginBottom: 16 }}>
          <p><strong>Instância:</strong> {d.instancia || '-'}</p>
          <p><strong>Circunscrição:</strong> {d.circunscricao || '-'}</p>
          <p><strong>Competência:</strong> {d.competencia || '-'}</p>
          <p><strong>Feito:</strong> {d.feito || '-'}</p>
          <p><strong>Classe:</strong> {d.classe || '-'}</p>
          <p><strong>Valor da Causa:</strong> {d.valor_causa || '-'}</p>
          <p><strong>Valor Atualizado:</strong> {d.valor_causa_atualizado || '-'}</p>
          <p><strong>Data Distribuição:</strong> {d.data_distribuicao || '-'}</p>
          <p><strong>Polo Ativo:</strong> {d.polo_ativo || '-'}</p>
          <p><strong>Polo Passivo:</strong> {d.polo_passivo || '-'}</p>
          <p><strong>Tipo Guia:</strong> {d.tipo_guia || '-'}</p>
          <p><strong>Pró-rata:</strong> {d.pro_rata ? 'Sim' : 'Não'}</p>
          <p><strong>Suspensão Exigibilidade:</strong> {d.suspensao_exigibilidade ? 'Sim' : 'Não'}</p>
          <p><strong>Área:</strong> {d.area_direito || '-'}</p>
        </div>

        {d.sucumbentes && (
          <div style={{ marginBottom: 16 }}>
            <h4>Sucumbentes</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#e9ecef' }}>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>%</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Nome</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>CPF/CNPJ</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Tipo</th>
                </tr>
              </thead>
              <tbody>
                {(Array.isArray(d.sucumbentes) ? d.sucumbentes : []).map((s: any, i: number) => (
                  <tr key={i}>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{s.percentual || s['% ou Fração'] || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{s.nome || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{s.cpf_cnpj || s.cpf || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{s.tipo || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <h4>Peças Processuais (IDs PJE)</h4>
          <ul>
            <li>Ofícios: {d.ids_oficios || '-'}</li>
            <li>Alvarás: {d.ids_alvaras || '-'}</li>
            <li>Traslados: {d.ids_traslados || '-'}</li>
            <li>Mandados: {d.ids_mandados || '-'}</li>
            <li>Cartas de Sentença: {d.ids_cartas_sentenca || '-'}</li>
            <li>AR: {d.ids_ar || '-'}</li>
            <li>AR/MP: {d.ids_armp || '-'}</li>
          </ul>
        </div>

        <div style={{ marginBottom: 16 }}>
          <h4>Outros Itens</h4>
          {d.outros_itens && Array.isArray(d.outros_itens) && d.outros_itens.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#e9ecef' }}>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Item Guia</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Item Cálculo</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Qtd</th>
                </tr>
              </thead>
              <tbody>
                {d.outros_itens.map((item: any, i: number) => (
                  <tr key={i}>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{item.item_guia || item.itemGuia || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{item.item_calculo || item.itemCalculo || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{item.quantidade || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>-</p>
          )}
        </div>

        <div style={{ marginBottom: 16 }}>
          <h4>Custas Pagas</h4>
          {d.custas_pagas && Array.isArray(d.custas_pagas) && d.custas_pagas.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#e9ecef' }}>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Data</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Valor</th>
                  <th style={{ border: '1px solid #ccc', padding: 8 }}>Guia</th>
                </tr>
              </thead>
              <tbody>
                {d.custas_pagas.map((cp: any, i: number) => (
                  <tr key={i}>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{cp.data || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{cp.valor || '-'}</td>
                    <td style={{ border: '1px solid #ccc', padding: 8 }}>{cp.numero_guia || cp.numeroGuia || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>-</p>
          )}
        </div>

        <h3 style={{ color: '#28a745' }}>Valor Total a Recolher: {d.valor_total_recolher || '-'}</h3>
      </div>

      <div>
        {d.screenshot_path && (
          <div style={{ marginBottom: 16 }}>
            <h4>Screenshot SISTJWEB</h4>
            <img src={`/screenshots/${p.numero}_sistjweb.png`} alt="Screenshot" style={{ maxWidth: '100%', border: '1px solid #ddd' }} />
          </div>
        )}

        <div style={{ background: '#fff3cd', padding: 12, borderRadius: 6, marginBottom: 16 }}>
          <strong>Avisos:</strong>
          <ul>
            {d.area_direito === 'default' && <li>⚠️ Área não mapeada — verifique Outros Itens manualmente</li>}
            {d.suspensao_exigibilidade && <li>⚠️ Suspensão de exigibilidade detectada — confirmar isenção</li>}
            {!d.sucumbente_nome && <li>⚠️ Sucumbente não identificado na sentença</li>}
          </ul>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4 }}><strong>Observações do Operador:</strong></label>
          <textarea
            value={obs}
            onChange={e => setObs(e.target.value)}
            rows={4}
            style={{ width: '100%', padding: 8 }}
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={aprovar} style={{ flex: 1, padding: 12, background: '#28a745', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
            ✅ Aprovar
          </button>
          <button onClick={rejeitar} style={{ flex: 1, padding: 12, background: '#dc3545', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
            ❌ Rejeitar
          </button>
        </div>
      </div>
    </div>
  )
}
