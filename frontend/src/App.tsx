import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import Button from './components/ui/Button'
import Login from './pages/Login'
import Fila from './pages/Fila'
import Detalhe from './pages/Detalhe'
import Historico from './pages/Historico'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

function Layout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth()
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-bold">Custas TJDFT</h1>
            <nav className="flex gap-4 text-sm">
              <Link
                to="/"
                className={`transition-colors hover:text-primary ${location.pathname === '/' ? 'font-medium text-primary' : 'text-muted-foreground'}`}
              >
                Fila de Aprovação
              </Link>
              <Link
                to="/historico"
                className={`transition-colors hover:text-primary ${location.pathname === '/historico' ? 'font-medium text-primary' : 'text-muted-foreground'}`}
              >
                Histórico
              </Link>
            </nav>
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            Sair
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <Layout>
                <Routes>
                  <Route path="/" element={<Fila />} />
                  <Route path="/detalhe/:id" element={<Detalhe />} />
                  <Route path="/historico" element={<Historico />} />
                </Routes>
              </Layout>
            </RequireAuth>
          }
        />
      </Routes>
    </AuthProvider>
  )
}
