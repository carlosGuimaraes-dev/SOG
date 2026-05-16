import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Detalhe from '../pages/Detalhe'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
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
})
