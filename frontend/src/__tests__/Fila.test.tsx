import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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

  it('exibe tentativas quando maior que zero', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00', tentativas: 3 },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('Tentativas: 3')).toBeInTheDocument()
    })
  })

  it('exibe badge de erro e borda vermelha quando erro_msg existe', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00', erro_msg: 'Falha na conexão' },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('Erro')).toBeInTheDocument()
    })
    const card = screen.getByText('0000012-75.2023.8.07.0001').closest('[class*="border-destructive"]') || screen.getByText('0000012-75.2023.8.07.0001').closest('[class*="bg-destructive"]')
    expect(card).not.toBeNull()
  })

  it('filtra processos por número de processo', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00' },
          { id: 2, numero: '0000023-12.2023.8.07.0002', status: 'aguardando_aprovacao', criado_em: '2024-01-02T10:00:00' },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
      expect(screen.getByText('0000023-12.2023.8.07.0002')).toBeInTheDocument()
    })

    const input = screen.getByLabelText(/buscar por número do processo/i)
    fireEvent.change(input, { target: { value: '0000012' } })

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
      expect(screen.queryByText('0000023-12.2023.8.07.0002')).not.toBeInTheDocument()
    })
  })

  it('exibe mensagem de estado vazio quando busca não encontra resultados', async () => {
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

    const input = screen.getByLabelText(/buscar por número do processo/i)
    fireEvent.change(input, { target: { value: '9999999' } })

    await waitFor(() => {
      expect(screen.getByText(/nenhum processo encontrado para esta busca/i)).toBeInTheDocument()
    })
  })

  it('exibe badge de prioridade Urgente quando há tentativas e erro_msg', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00', tentativas: 2, erro_msg: 'Falha' },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('Urgente')).toBeInTheDocument()
    })
  })

  it('exibe badge de prioridade Alto Valor quando valor > R$ 50.000', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: '2024-01-01T10:00:00', valor_total_recolher: 'R$ 75.000,00' },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('Alto Valor')).toBeInTheDocument()
    })
  })

  it('exibe badge de prioridade Antigo quando processo tem mais de 7 dias', async () => {
    const dataAntiga = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
    mockedGet.mockResolvedValueOnce({
      data: {
        aguardando_aprovacao: [
          { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aguardando_aprovacao', criado_em: dataAntiga },
        ],
        pendente_manual: [],
      },
    })
    renderFila()

    await waitFor(() => {
      expect(screen.getByText('Antigo')).toBeInTheDocument()
    })
  })

  it('limpa busca ao clicar no botão de limpar', async () => {
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

    const input = screen.getByLabelText(/buscar por número do processo/i)
    fireEvent.change(input, { target: { value: '9999999' } })

    await waitFor(() => {
      expect(screen.getByText(/nenhum processo encontrado para esta busca/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByLabelText(/limpar busca/i))

    await waitFor(() => {
      expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
    })
  })
})
