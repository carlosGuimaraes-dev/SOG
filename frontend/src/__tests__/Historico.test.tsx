import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Historico from '../pages/Historico'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../lib/api'
const mockedGet = vi.mocked(api.get)

function renderHistorico() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <Historico />
      </ToastProvider>
    </BrowserRouter>
  )
}

describe('Historico', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exibe loading inicial', () => {
    mockedGet.mockReturnValueOnce(new Promise(() => {}))
    renderHistorico()
    expect(screen.getAllByRole('status', { name: /carregando/i }).length).toBeGreaterThan(0)
  })

  it('lista registros do histórico', async () => {
    mockedGet.mockResolvedValueOnce({
      data: [
        { id: 1, numero: '0000012-75.2023.8.07.0001', polo_ativo: 'João', valor_total_recolher: 'R$ 1.000,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: 'OK' },
        { id: 2, numero: '0000023-12.2023.8.07.0002', polo_ativo: 'Maria', valor_total_recolher: 'R$ 2.000,00', status: 'rejeitado', atualizado_em: '2024-01-10T10:00:00', obs_operador: 'Falta doc' },
      ],
    })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
      expect(screen.getByText('0000023-12.2023.8.07.0002')).toBeInTheDocument()
    })
  })

  it('exibe estado vazio quando não há registros', async () => {
    mockedGet.mockResolvedValueOnce({ data: [] })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText(/nenhum registro no histórico/i)).toBeInTheDocument()
    })
  })

  it('filtra por status', async () => {
    mockedGet.mockResolvedValueOnce({
      data: [
        { id: 1, numero: '0000012-75.2023.8.07.0001', polo_ativo: 'João', valor_total_recolher: 'R$ 1.000,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
        { id: 2, numero: '0000023-12.2023.8.07.0002', polo_ativo: 'Maria', valor_total_recolher: 'R$ 2.000,00', status: 'rejeitado', atualizado_em: '2024-01-10T10:00:00', obs_operador: '' },
      ],
    })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'rejeitado' } })

    await waitFor(() => {
      expect(screen.queryByText('0000012-75.2023.8.07.0001')).not.toBeInTheDocument()
      expect(screen.getByText('0000023-12.2023.8.07.0002')).toBeInTheDocument()
    })
  })

  it('filtra por valor mínimo', async () => {
    mockedGet.mockResolvedValueOnce({
      data: [
        { id: 1, numero: 'A', polo_ativo: '', valor_total_recolher: 'R$ 500,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
        { id: 2, numero: 'B', polo_ativo: '', valor_total_recolher: 'R$ 5.000,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
      ],
    })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
      expect(screen.getByText('B')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/valor mínimo/i), { target: { value: '1000' } })

    await waitFor(() => {
      expect(screen.queryByText('A')).not.toBeInTheDocument()
      expect(screen.getByText('B')).toBeInTheDocument()
    })
  })

  it('limpa filtros ao clicar em limpar', async () => {
    mockedGet.mockResolvedValueOnce({
      data: [
        { id: 1, numero: 'A', polo_ativo: '', valor_total_recolher: 'R$ 500,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
        { id: 2, numero: 'B', polo_ativo: '', valor_total_recolher: 'R$ 5.000,00', status: 'rejeitado', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
      ],
    })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'rejeitado' } })

    await waitFor(() => {
      expect(screen.queryByText('A')).not.toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /limpar filtros/i }))

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
      expect(screen.getByText('B')).toBeInTheDocument()
    })
  })

  it('reseta paginação para página 1 quando filtro muda', async () => {
    const data = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      numero: `PROC-${String(i + 1).padStart(3, '0')}`,
      polo_ativo: '',
      valor_total_recolher: 'R$ 1.000,00',
      status: i < 15 ? 'emitido' : 'rejeitado',
      atualizado_em: '2024-01-15T10:00:00',
      obs_operador: '',
    }))
    mockedGet.mockResolvedValueOnce({ data })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('PROC-001')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /próxima página/i }))

    await waitFor(() => {
      expect(screen.getByText('PROC-021')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'rejeitado' } })

    await waitFor(() => {
      expect(screen.getByText('PROC-016')).toBeInTheDocument()
    })
  })

  it('exibe mensagem de estado vazio para filtros sem resultados', async () => {
    mockedGet.mockResolvedValueOnce({
      data: [
        { id: 1, numero: 'A', polo_ativo: '', valor_total_recolher: 'R$ 500,00', status: 'emitido', atualizado_em: '2024-01-15T10:00:00', obs_operador: '' },
      ],
    })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'rejeitado' } })

    await waitFor(() => {
      expect(screen.getByText(/nenhum registro corresponde aos filtros/i)).toBeInTheDocument()
    })
  })

  it('renderiza botão de exportar CSV', async () => {
    mockedGet.mockResolvedValueOnce({ data: [] })
    renderHistorico()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /exportar histórico em csv/i })).toBeInTheDocument()
    })
  })
})
