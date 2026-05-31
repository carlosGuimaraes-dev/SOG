import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Detalhe from '../pages/Detalhe'

const mockUsePollingStatus = vi.fn<[string | undefined, number?], ReturnType<typeof import('../hooks/usePollingStatus').usePollingStatus>>(() => ({
  data: null,
  loading: false,
  error: null,
  stop: vi.fn(),
}))

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../hooks/usePollingStatus', () => ({
  usePollingStatus: (...args: Parameters<typeof import('../hooks/usePollingStatus').usePollingStatus>) => mockUsePollingStatus(...args),
}))

import api from '../lib/api'
const mockedGet = vi.mocked(api.get)
const mockedPost = vi.mocked(api.post)

const mockProcesso = {
  processo: {
    id: 1,
    numero: '0000012-75.2023.8.07.0001',
    status: 'aguardando_aprovacao',
    criado_em: '2024-01-01T10:00:00',
  },
  dados: {
    instancia: '1ª Instância',
    circunscricao: 'Brasília',
    competencia: 'Cível',
    feito: 'Feito Teste',
    classe: 'Ação de Cobrança',
    valor_causa: 'R$ 10.000,00',
    polo_ativo: 'Autor Teste',
    polo_passivo: 'Réu Teste',
    area_direito: 'civel',
    sucumbente_nome: 'Réu Teste',
    screenshot_path: '/dados/screenshots/test.png',
    valor_total_recolher: 'R$ 500,00',
    sucumbentes: [
      { nome: 'Réu Teste', percentual: '100%', cpf_cnpj: '123.456.789-00', tipo: 'Réu' },
    ],
    obs_operador: '',
  },
  logs: [],
  documentos: [],
}

function processoComStatus(status: string, extraProcesso = {}) {
  return {
    ...mockProcesso,
    processo: {
      ...mockProcesso.processo,
      status,
      ...extraProcesso,
    },
  }
}

function renderDetalhe() {
  return render(
    <MemoryRouter initialEntries={['/detalhe/1']}>
      <ToastProvider>
        <Routes>
          <Route path="/detalhe/:id" element={<Detalhe />} />
          <Route path="/" element={<div data-testid="fila">Fila</div>} />
        </Routes>
      </ToastProvider>
    </MemoryRouter>
  )
}

describe('Detalhe', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn(() => Promise.resolve({ ok: false } as Response))
    mockUsePollingStatus.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      stop: vi.fn(),
    })
  })

  it('renderiza loading inicial', () => {
    mockedGet.mockReturnValueOnce(new Promise(() => {}))
    renderDetalhe()
    expect(screen.getAllByRole('status', { name: /carregando/i }).length).toBeGreaterThan(0)
  })

  it('exibe dados do processo após carregar', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText(/Processo 0000012-75.2023.8.07.0001/i)).toBeInTheDocument()
      expect(screen.getByText('1ª Instância')).toBeInTheDocument()
      expect(screen.getByText('Brasília')).toBeInTheDocument()
    })
  })

  it('chama aprovar ao clicar no botão', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    mockedPost.mockResolvedValueOnce({ data: {} })
    vi.stubGlobal('confirm', () => true)

    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /aprovar processo/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /aprovar processo/i }))

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith('/aprovar/1')
    })
    vi.unstubAllGlobals()
  })

  it('chama rejeitar ao clicar no botão', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    mockedPost.mockResolvedValueOnce({ data: {} })
    vi.stubGlobal('confirm', () => true)

    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /rejeitar processo/i })).toBeInTheDocument()
    })

    const textarea = screen.getByLabelText(/observações do operador/i)
    fireEvent.change(textarea, { target: { value: 'Obs de teste' } })
    fireEvent.click(screen.getByRole('button', { name: /rejeitar processo/i }))

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith('/rejeitar/1', { observacao: 'Obs de teste' })
    })
    vi.unstubAllGlobals()
  })

  it('não exibe reprocessar para status não elegível', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /aprovar processo/i })).toBeInTheDocument()
    })

    expect(screen.queryByRole('button', { name: /reprocessar processo/i })).not.toBeInTheDocument()
  })

  it.each(['erro', 'pendente_manual', 'rejeitado'])(
    'chama reprocessar para status %s',
    async (status) => {
      mockedGet
        .mockResolvedValueOnce({ data: processoComStatus(status) })
        .mockResolvedValueOnce({
          data: processoComStatus(status, {
            reprocessar_solicitado_em: '2026-05-30T00:00:00',
          }),
        })
      mockedPost.mockResolvedValueOnce({ data: {} })
      vi.stubGlobal('confirm', () => true)

      renderDetalhe()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reprocessar processo/i })).toBeInTheDocument()
      })

      const textarea = screen.getByLabelText(/observações do operador/i)
      fireEvent.change(textarea, { target: { value: 'Motivo teste' } })
      fireEvent.click(screen.getByRole('button', { name: /reprocessar processo/i }))

      await waitFor(() => {
        expect(mockedPost).toHaveBeenCalledWith('/processos/1/reprocessar', {
          motivo: 'Motivo teste',
        })
      })
      vi.unstubAllGlobals()
    }
  )

  it('bloqueia reprocessar quando já existe solicitação pendente', async () => {
    mockedGet.mockResolvedValueOnce({
      data: processoComStatus('erro', {
        reprocessar_solicitado_em: '2026-05-30T00:00:00',
      }),
    })
    renderDetalhe()

    const button = await screen.findByRole('button', { name: /reprocessar processo/i })

    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('Reprocessamento solicitado')
  })

  it('exibe tabela de sucumbentes', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Sucumbentes')).toBeInTheDocument()
    })
    const table = screen.getByRole('table')
    expect(table).toHaveTextContent('100%')
    expect(table).toHaveTextContent('Réu Teste')
    expect(table).toHaveTextContent('123.456.789-00')
  })

  it('exibe link Abrir no PJE com target blank', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /abrir processo no pje/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
      expect(link.getAttribute('href')).toContain('nrProcesso=')
    })
  })

  it('exibe resumo do preenchimento automático', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Resumo do Preenchimento Automático')).toBeInTheDocument()
      expect(screen.getByText('R$ 500,00')).toBeInTheDocument()
    })
    // Réu Teste aparece em vários lugares (resumo + tabela sucumbentes)
    expect(screen.getAllByText('Réu Teste').length).toBeGreaterThanOrEqual(1)
  })

  it('exibe banner de erro quando processo tem erro_msg', async () => {
    const mockComErro = {
      ...mockProcesso,
      processo: { ...mockProcesso.processo, erro_msg: 'Falha na conexão com PJE' },
    }
    mockedGet.mockResolvedValueOnce({ data: mockComErro })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Falha na conexão com PJE')).toBeInTheDocument()
    })
  })

  it('não exibe banner de erro quando processo não tem erro_msg', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  it('exibe timeline de logs quando há logs', async () => {
    const mockComLogs = {
      ...mockProcesso,
      logs: [
        { id: 1, processo_id: 1, etapa: 'Login', status: 'ok' as const, mensagem: 'Sucesso', criado_em: '2024-01-15T10:00:00' },
      ],
    }
    mockedGet.mockResolvedValueOnce({ data: mockComLogs })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Logs de Execução')).toBeInTheDocument()
      expect(screen.getByText('Login')).toBeInTheDocument()
    })
  })

  it('exibe estado vazio de logs quando não há logs', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Logs de Execução')).toBeInTheDocument()
      expect(screen.getByText('Nenhum log registrado')).toBeInTheDocument()
    })
  })

  it('exibe documentos PJE quando há documentos', async () => {
    const mockComDocs = {
      ...mockProcesso,
      documentos: [
        { id: 1, processo_id: 1, doc_id: 'doc-1', tipo: 'Petição Inicial', data_assinatura: '2024-01-15T10:00:00', nome: 'Petição.pdf' },
      ],
    }
    mockedGet.mockResolvedValueOnce({ data: mockComDocs })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Documentos PJE')).toBeInTheDocument()
      expect(screen.getByText('Petição Inicial')).toBeInTheDocument()
      expect(screen.getByText('Petição.pdf')).toBeInTheDocument()
    })
  })

  it('exibe estado vazio de documentos quando não há documentos', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Documentos PJE')).toBeInTheDocument()
      expect(screen.getByText('Nenhum documento extraído')).toBeInTheDocument()
    })
  })

  it('exibe compensação quando há dados', async () => {
    const mockComComp = {
      ...mockProcesso,
      dados: {
        ...mockProcesso.dados,
        compensacao: [
          { data: '2024-01-15', valor: 'R$ 1.000,00', numero_guia: '12345' },
        ],
      },
    }
    mockedGet.mockResolvedValueOnce({ data: mockComComp })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Compensação')).toBeInTheDocument()
      expect(screen.getByText('R$ 1.000,00')).toBeInTheDocument()
      expect(screen.getByText('12345')).toBeInTheDocument()
    })
  })

  it('exibe estado vazio de compensação quando não há dados', async () => {
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Compensação')).toBeInTheDocument()
      expect(screen.getByText('Nenhuma compensação')).toBeInTheDocument()
    })
  })

  it('exibe EmissaoStatus quando processo está aprovado', async () => {
    const mockAprovado = {
      ...mockProcesso,
      processo: { ...mockProcesso.processo, status: 'aprovado' },
    }
    mockedGet.mockResolvedValueOnce({ data: mockAprovado })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText('Status da Emissão')).toBeInTheDocument()
      expect(screen.getByText('Emissão em andamento...')).toBeInTheDocument()
    })
  })

  it('exibe link do demonstrativo PDF', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({ ok: true } as Response)
    mockedGet.mockResolvedValueOnce({ data: mockProcesso })
    renderDetalhe()

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /abrir demonstrativo em pdf/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('target', '_blank')
      expect(link.getAttribute('href')).toContain('_demonstrativo.pdf')
    })
  })

  it('exibe aviso de valor alto quando valor > R$ 50.000', async () => {
    const mockValorAlto = {
      ...mockProcesso,
      dados: {
        ...mockProcesso.dados,
        valor_total_recolher: 'R$ 75.000,00',
      },
    }
    mockedGet.mockResolvedValueOnce({ data: mockValorAlto })
    renderDetalhe()

    await waitFor(() => {
      expect(screen.getByText(/Valor total muito alto/i)).toBeInTheDocument()
    })
  })
})
