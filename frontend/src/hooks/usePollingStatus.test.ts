import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { usePollingStatus } from './usePollingStatus'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../lib/api'
const mockedGet = vi.mocked(api.get)

describe('usePollingStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('não faz nada quando id é undefined', () => {
    const { result } = renderHook(() => usePollingStatus(undefined))
    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('carrega status inicial imediatamente', async () => {
    mockedGet.mockResolvedValueOnce({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aprovado', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
    })

    const { result } = renderHook(() => usePollingStatus('1', 50))

    await waitFor(() => {
      expect(result.current.data?.processo.status).toBe('aprovado')
    })
  })

  it('para polling quando status muda para emitido', async () => {
    mockedGet
      .mockResolvedValueOnce({
        data: {
          processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aprovado', criado_em: '2024-01-01T10:00:00' },
          dados: {},
          logs: [],
          documentos: [],
        },
      })
      .mockResolvedValueOnce({
        data: {
          processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'emitido', criado_em: '2024-01-01T10:00:00' },
          dados: {},
          logs: [],
          documentos: [],
        },
      })

    const { result } = renderHook(() => usePollingStatus('1', 100))

    await waitFor(() => {
      expect(result.current.data?.processo.status).toBe('emitido')
    })

    // Após mudar para emitido, não deve haver mais chamadas
    await new Promise((r) => setTimeout(r, 250))
    expect(mockedGet).toHaveBeenCalledTimes(2)
  })

  it('para polling quando status muda para erro', async () => {
    mockedGet
      .mockResolvedValueOnce({
        data: {
          processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aprovado', criado_em: '2024-01-01T10:00:00' },
          dados: {},
          logs: [],
          documentos: [],
        },
      })
      .mockResolvedValueOnce({
        data: {
          processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'erro', criado_em: '2024-01-01T10:00:00', erro_msg: 'Falha na emissão' },
          dados: {},
          logs: [],
          documentos: [],
        },
      })

    const { result } = renderHook(() => usePollingStatus('1', 100))

    await waitFor(() => {
      expect(result.current.data?.processo.status).toBe('erro')
    })

    await new Promise((r) => setTimeout(r, 250))
    expect(mockedGet).toHaveBeenCalledTimes(2)
  })

  it('define erro quando a API falha', async () => {
    mockedGet.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => usePollingStatus('1', 50))

    await waitFor(() => {
      expect(result.current.error).toBe('Erro ao consultar status da emissão')
    })
  })

  it('stop interrompe polling manualmente', async () => {
    mockedGet.mockResolvedValue({
      data: {
        processo: { id: 1, numero: '0000012-75.2023.8.07.0001', status: 'aprovado', criado_em: '2024-01-01T10:00:00' },
        dados: {},
        logs: [],
        documentos: [],
      },
    })

    const { result } = renderHook(() => usePollingStatus('1', 200))

    await waitFor(() => {
      expect(result.current.data?.processo.status).toBe('aprovado')
    })

    result.current.stop()

    await new Promise((r) => setTimeout(r, 300))
    expect(mockedGet).toHaveBeenCalledTimes(1)
  })
})
