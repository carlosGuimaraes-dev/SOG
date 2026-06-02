import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from '../App'

vi.mock('../lib/auth', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: { username: 'operador' },
    authRequired: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}))

vi.mock('../pages/CicloAtual', () => ({
  default: () => <div>Página Ciclo Atual</div>,
}))

vi.mock('../pages/Fila', () => ({
  default: () => <div>Página Processos</div>,
}))

vi.mock('../pages/Historico', () => ({
  default: () => <div>Página Histórico</div>,
}))

describe('App shell autenticado', () => {
  it('usa Ciclo atual como home e renderiza tabs principais', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Página Ciclo Atual')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ciclo atual' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Processos' })).toHaveAttribute('href', '/processos')
    expect(screen.getByRole('link', { name: 'Histórico' })).toHaveAttribute('href', '/historico')
  })
})
