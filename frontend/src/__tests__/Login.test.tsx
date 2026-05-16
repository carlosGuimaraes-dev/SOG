import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../lib/auth'
import { ToastProvider } from '../components/ToastProvider'
import Login from '../pages/Login'

vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(() => Promise.reject(new Error('401'))),
  },
}))

import api from '../lib/api'

const mockedPost = vi.mocked(api.post)

function renderLogin() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Login />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza formulario de login', async () => {
    renderLogin()
    await waitFor(() => {
      expect(screen.getByLabelText('Usuário')).toBeInTheDocument()
    })
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
  })

  it('exibe erro ao falhar login', async () => {
    mockedPost.mockRejectedValueOnce(new Error('401'))
    renderLogin()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Usuário'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(screen.getByText(/usuário ou senha incorretos/i)).toBeInTheDocument()
    })
  })

  it('loga com sucesso e redireciona', async () => {
    mockedPost.mockResolvedValueOnce({ data: {} })
    const mockedGet = vi.mocked(api.get)
    mockedGet.mockResolvedValueOnce({ data: { username: 'admin' } })
    renderLogin()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Usuário'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'secret' } })
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith('/auth/login', { username: 'admin', password: 'secret' })
      expect(mockedGet).toHaveBeenCalledWith('/auth/me')
    })
  })
})
