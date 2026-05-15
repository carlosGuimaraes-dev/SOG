import { Routes, Route } from 'react-router-dom'
import Fila from './pages/Fila'
import Detalhe from './pages/Detalhe'
import Historico from './pages/Historico'

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <header style={{ borderBottom: '1px solid #ddd', marginBottom: 24, paddingBottom: 16 }}>
        <h1 style={{ margin: 0 }}>Custas TJDFT — Dashboard</h1>
        <nav style={{ marginTop: 12, display: 'flex', gap: 16 }}>
          <a href="/">Fila de Aprovação</a>
          <a href="/historico">Histórico</a>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Fila />} />
        <Route path="/detalhe/:id" element={<Detalhe />} />
        <Route path="/historico" element={<Historico />} />
      </Routes>
    </div>
  )
}
