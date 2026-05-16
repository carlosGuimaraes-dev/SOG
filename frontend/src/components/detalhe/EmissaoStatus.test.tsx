import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import EmissaoStatus from './EmissaoStatus'

vi.mock('../../hooks/usePollingStatus', () => ({
  usePollingStatus: vi.fn(),
}))

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../../components/ToastProvider', () => ({
  useToast: vi.fn(),
}))

import { usePollingStatus } from '../../hooks/usePollingStatus'
import { useToast } from '../../components/ToastProvider'

const mockedUsePollingStatus = vi.mocked(usePollingStatus)
const mockedUseToast = vi.mocked(useToast)

function renderEmissaoStatus(processoId: number | string = 1) {
  return render(
    <MemoryRouter>
      <EmissaoStatus processoId={processoId} />
    </MemoryRouter>
  )
}

describe('EmissaoStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedUseToast.mockReturnValue({ toasts: [], addToast: vi.fn(), removeToast: vi.fn() })
  })

  it('renderiza spinner quando status é aprovado', () => {
    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aprovado', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(screen.getByText('Emissão em andamento...')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renderiza sucesso quando status é emitido', () => {
    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'emitido', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(screen.getByText('✅ Emitido com sucesso')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /voltar para fila/i })).toBeInTheDocument()
  })

  it('renderiza erro quando status é erro', () => {
    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'erro', criado_em: '2024-01-01T10:00:00', erro_msg: 'Falha na conexão' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(screen.getByText('❌ Falha na emissão')).toBeInTheDocument()
    expect(screen.getByText('Falha na conexão')).toBeInTheDocument()
  })

  it('renderiza erro sem mensagem quando erro_msg está ausente', () => {
    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'erro', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(screen.getByText('❌ Falha na emissão')).toBeInTheDocument()
  })

  it('chama addToast com success quando status muda para emitido', () => {
    const addToast = vi.fn()
    mockedUseToast.mockReturnValue({ toasts: [], addToast, removeToast: vi.fn() })

    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'emitido', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(addToast).toHaveBeenCalledWith('Guia emitida com sucesso!', 'success')
  })

  it('chama addToast com error quando status muda para erro', () => {
    const addToast = vi.fn()
    mockedUseToast.mockReturnValue({ toasts: [], addToast, removeToast: vi.fn() })

    mockedUsePollingStatus.mockReturnValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'erro', criado_em: '2024-01-01T10:00:00', erro_msg: 'Falha na conexão' },
        dados: {},
        logs: [],
        documentos: [],
      },
      loading: false,
      error: null,
      stop: vi.fn(),
    })

    renderEmissaoStatus()
    expect(addToast).toHaveBeenCalledWith('Falha na emissão da guia', 'error')
  })
})
