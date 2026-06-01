import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import AgenteStatusBar from './AgenteStatusBar'
import api from '../../lib/api'
import { ENDPOINTS } from '../../lib/endpoints'
import { useToast } from '../ToastProvider'

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../ToastProvider', () => ({
  useToast: vi.fn(),
}))

const mockedGet = vi.mocked(api.get)
const mockedPost = vi.mocked(api.post)
const mockedUseToast = vi.mocked(useToast)

const CICLO_FIXTURE = {
  uuid: 'ciclo-1',
  rotulo: 'Ciclo 31/05 10:00',
  status: 'executando',
  total_membros: 12,
  total_novos: 4,
  total_rearmados: 3,
  total_concluidos: 5,
  total_erros: 1,
}

function mockStatusBarRequests(statusData: Record<string, unknown>, cicloData = CICLO_FIXTURE) {
  mockedGet.mockImplementation(async (url: string) => {
    if (url === ENDPOINTS.AGENTE_STATUS) {
      return { data: statusData }
    }
    if (url === ENDPOINTS.AGENTE_CICLO_ATUAL) {
      return { data: cicloData }
    }
    if (url === ENDPOINTS.AGENTE_ULTIMO_CICLO) {
      return { data: cicloData }
    }
    throw new Error(`unexpected endpoint: ${url}`)
  })
}

describe('AgenteStatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedUseToast.mockReturnValue({ toasts: [], addToast: vi.fn(), removeToast: vi.fn() })
  })

  it('expõe ciclo ativo de forma explícita durante a execução', async () => {
    mockStatusBarRequests({
      status: 'executando',
      mensagem: 'Iteração em andamento.',
      online: true,
      ciclo_uuid: 'ciclo-1',
      pode_iniciar: false,
      pode_parar: true,
      relogin_required: false,
    })

    render(<AgenteStatusBar />)

    expect(await screen.findByText('Ciclo ativo')).toBeInTheDocument()
    expect(screen.getByText('Ciclo 31/05 10:00')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar agente de automação/i })).toHaveTextContent(
      '▶ Iniciar novo ciclo'
    )
    expect(screen.getByRole('button', { name: /iniciar agente de automação/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /parar agente de automação/i })).toBeEnabled()
  })

  it('marca relogin pendente e orienta a retomada após novo login', async () => {
    mockStatusBarRequests({
      status: 'aguardando_login',
      mensagem: 'Sessão pje expirada.',
      online: true,
      ciclo_uuid: 'ciclo-login',
      pode_iniciar: true,
      pode_parar: false,
      relogin_required: true,
    }, {
      ...CICLO_FIXTURE,
      uuid: 'ciclo-login',
      status: 'aguardando_login',
    })

    render(<AgenteStatusBar />)

    expect(await screen.findByText('Relogin pendente')).toBeInTheDocument()
    expect(screen.getByText('Sessão PJe pendente')).toBeInTheDocument()
    expect(screen.getByText(/Faça login no Chromium aberto pelo agente desktop/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar agente de automação/i })).toHaveTextContent(
      '▶ Retomar após login'
    )
    expect(screen.getByRole('button', { name: /parar agente de automação/i })).toBeDisabled()
  })

  it('diferencia sessão SISTJWEB pendente', async () => {
    mockStatusBarRequests({
      status: 'aguardando_login',
      mensagem: 'Sessão sistjweb expirada.',
      online: true,
      ciclo_uuid: 'ciclo-login',
      pode_iniciar: true,
      pode_parar: false,
      relogin_required: true,
    }, {
      ...CICLO_FIXTURE,
      uuid: 'ciclo-login',
      status: 'aguardando_login',
    })

    render(<AgenteStatusBar />)

    expect(await screen.findByText('Sessão SISTJWEB pendente')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar agente de automação/i })).toHaveTextContent(
      '▶ Retomar após login'
    )
  })

  it('trata erro pausado como retomada do mesmo ciclo e usa a mensagem real da API', async () => {
    const addToast = vi.fn()
    mockedUseToast.mockReturnValue({ toasts: [], addToast, removeToast: vi.fn() })
    mockStatusBarRequests({
      status: 'erro_pausado',
      mensagem: 'Falha temporária.',
      online: true,
      ciclo_uuid: 'ciclo-erro',
      pode_iniciar: true,
      pode_parar: false,
      relogin_required: false,
    }, {
      ...CICLO_FIXTURE,
      uuid: 'ciclo-erro',
      status: 'erro_pausado',
    })
    mockedPost.mockResolvedValue({
      data: {
        message: 'Ciclo retomado.',
        resumed: true,
      },
    })

    render(<AgenteStatusBar />)

    const iniciar = await screen.findByRole('button', { name: /iniciar agente de automação/i })
    expect(iniciar).toHaveTextContent('▶ Retomar ciclo')

    fireEvent.click(iniciar)

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith(ENDPOINTS.AGENTE_INICIAR)
      expect(addToast).toHaveBeenCalledWith('Ciclo retomado.', 'info')
    })
  })
})
