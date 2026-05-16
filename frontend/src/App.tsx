import React, { Suspense } from 'react'
import { Routes, Route, Navigate, Link, useLocation, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import { ToastProvider } from './components/ToastProvider'
import ErrorBoundary from './components/ErrorBoundary'
import ThemeToggle from './components/ThemeToggle'
import Button from './components/ui/Button'
import Skeleton from './components/ui/Skeleton'
import Login from './pages/Login'
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
                aria-label="Ir para fila de aprovação"
              >
                Fila de Aprovação
              </Link>
              <Link
                to="/historico"
                className={`transition-colors hover:text-primary ${location.pathname === '/historico' ? 'font-medium text-primary' : 'text-muted-foreground'}`}
                aria-label="Ir para histórico"
              >
                Histórico
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={logout} aria-label="Sair da conta">
              Sair
            </Button>
          </div>
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
                <Route path="/" element={<Fila />} />
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
