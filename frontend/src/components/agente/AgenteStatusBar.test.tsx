import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import AgenteStatusBar from './AgenteStatusBar'
import { ToastProvider } from '../ToastProvider'

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../../lib/api'

const mockedGet = vi.mocked(api.get)

describe('AgenteStatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza diagnóstico para suporte com detalhes técnicos', async () => {
    mockedGet
      .mockResolvedValueOnce({
        data: {
          status: 'desconhecido',
          mensagem: 'Agente offline',
          online: false,
          runtime_diagnostic: {
            overall_status: 'error',
            operator_message: 'Contate o suporte em (61) 3210-4321 ou suporte@tjdft.jus.br.',
            support_summary: 'Etapa com falha: Docker daemon.',
            support_contact: {
              phone: '(61) 3210-4321',
              email: 'suporte@tjdft.jus.br',
              is_placeholder: false,
            },
            steps: [
              {
                id: 'docker_daemon',
                label: 'Docker daemon',
                status: 'error',
                summary: 'Docker daemon indisponível.',
                technical_detail: 'Cannot connect to the Docker daemon',
              },
            ],
          },
        },
      })
      .mockResolvedValueOnce({ data: null })
      .mockResolvedValueOnce({ data: null })

    render(
      <ToastProvider>
        <AgenteStatusBar />
      </ToastProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Diagnóstico para suporte')).toBeInTheDocument()
    })
    expect(screen.getByText(/Contato:\s*\(61\) 3210-4321/)).toBeInTheDocument()

    fireEvent.click(screen.getByText('Detalhes técnicos'))

    await waitFor(() => {
      expect(screen.getByText('Docker daemon')).toBeInTheDocument()
      expect(screen.getByText('Cannot connect to the Docker daemon')).toBeInTheDocument()
    })
  })
})
