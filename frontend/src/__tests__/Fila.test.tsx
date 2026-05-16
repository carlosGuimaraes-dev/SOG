import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Fila from '../pages/Fila'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../lib/api'
const mockedGet = vi.mocked(api.get)

function renderFila() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <Fila />
      </ToastProvider>
    </BrowserRouter>
  )
}

describe('Fila', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exibe loading inicial', () => {
    mockedGet.mockReturnValueOnce(new Promise(() => {}))
    renderFila()
    expect(screen.getAllByRole('status', { name: /carregando/i }).length).toBeGreaterThan(0)
  })

  it('lista processos aguardando aprovação', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00' },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: /revisar processo/i })).toHaveAttribute('href', '/detalhe/1')
  })

  it('mostra estado vazio quando não há processos', async () => {
    mockedGet.mockResolvedValueOnce({
      data: { aguardando_aprovacao: [], pendente_manual: [] },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText(/nenhum processo aguardando aprovação/i)).toBeInTheDocument()
    })
  })

  it('lista processos pendentes manuais com badge', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [],
        pendente_manual: [
          { id: 2, numero: '0000023-12.2023.8.07.0002', status: 'pendente_manual', criado_em: '2024-01-02T10:00:00' },
        ],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('0000023-12.2023.8.07.0002')).toBeInTheDocument()
      expect(screen.getByText('Manual')).toBeInTheDocument()
    })
  })
})
