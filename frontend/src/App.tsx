import React, { Suspense } from 'react'
import { Routes, Route, Navigate, Link, useLocation, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import { ToastProvider } from './components/ToastProvider'
import ErrorBoundary from './components/ErrorBoundary'
import ThemeToggle from './components/ThemeToggle'
import Button from './components/ui/Button'
import Skeleton from './components/ui/Skeleton'
import Login from './pages/Login'
import CicloAtual from './pages/CicloAtual'
import Fila from './pages/Fila'

const Detalhe = React.lazy(() => import('./pages/Detalhe'))
const Historico = React.lazy(() => import('./pages/Historico'))

function RequireAuth() {
  const { user, isLoading } = useAuth()
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div
          className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"
          role="status"
          aria-label="Carregando autenticação"
        />
      </div>
    )
  }
  return user ? <Outlet /> : <Navigate to="/login" replace />
}

function Layout() {
  const { authRequired, logout } = useAuth()
  const location = useLocation()
  const navItems = [
    { to: '/', label: 'Ciclo atual', active: location.pathname === '/' },
    { to: '/processos', label: 'Processos', active: location.pathname.startsWith('/processos') || location.pathname.startsWith('/detalhe/') },
    { to: '/historico', label: 'Histórico', active: location.pathname.startsWith('/historico') },
  ]

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-xl font-bold">Custas TJDFT</h1>
              <p className="text-sm text-muted-foreground">Dashboard operacional para controle e emissão final.</p>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              {authRequired && (
                <Button variant="ghost" size="sm" onClick={logout} aria-label="Sair da conta">
                  Sair
                </Button>
              )}
            </div>
          </div>
          <nav className="inline-flex w-full flex-wrap gap-2 rounded-lg border border-border bg-muted/40 p-1 text-sm" aria-label="Navegação principal do dashboard">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`inline-flex min-h-10 flex-1 items-center justify-center rounded-md px-3 py-2 font-medium transition-colors ${
                  item.active
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-background hover:text-foreground'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <ErrorBoundary>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<RequireAuth />}>
              <Route element={<Layout />}>
                <Route path="/" element={<CicloAtual />} />
                <Route path="/processos" element={<Fila />} />
                <Route
                  path="/detalhe/:id"
                  element={
                    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
                      <Detalhe />
                    </Suspense>
                  }
                />
                <Route
                  path="/historico"
                  element={
                    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
                      <Historico />
                    </Suspense>
                  }
                />
              </Route>
            </Route>
          </Routes>
        </ErrorBoundary>
      </ToastProvider>
    </AuthProvider>
  )
}
