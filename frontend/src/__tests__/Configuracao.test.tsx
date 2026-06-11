import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Configuracao from '../pages/Configuracao'
import { ENDPOINTS } from '../lib/endpoints'

const fetchMock = vi.fn()

vi.stubGlobal('fetch', fetchMock)

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../lib/auth', () => ({
  useAuth: () => ({
    authRequired: false,
  }),
}))

vi.mock('../components/agente/AgenteStatusBar', () => ({
  default: () => <div>Status do agente</div>,
}))

import api from '../lib/api'

const mockedGet = vi.mocked(api.get)

const dashboardResumo = {
  agente_online: true,
  agente_status: 'aguardando_login',
  tarefas_pendentes: 2,
  tarefas_executando: 1,
  pje: {
    sistema: 'pje',
    logado: false,
    mensagem: 'Sessão inativa',
    ultima_verificacao: '2026-06-03T05:00:00Z',
  },
  sistj: {
    sistema: 'sistj',
    logado: true,
    mensagem: 'Sessão ativa',
    ultima_verificacao: '2026-06-03T05:01:00Z',
  },
}

const agenteStatus = {
  status: 'aguardando_login',
  mensagem: 'Sessão PJe pendente',
  online: true,
  atualizado_em: '2026-06-03T05:02:00Z',
  relogin_required: true,
}

function mockApi() {
  mockedGet.mockImplementation((url: string) => {
    if (url === ENDPOINTS.DASHBOARD_SESSOES) {
      return Promise.resolve({ data: dashboardResumo })
    }

    if (url === ENDPOINTS.AGENTE_STATUS) {
      return Promise.resolve({ data: agenteStatus })
    }

    return Promise.resolve({ data: null })
  })
}

function renderConfiguracao() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <Configuracao />
      </ToastProvider>
    </BrowserRouter>,
  )
}

describe('Configuração', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchMock.mockReset()
    mockApi()
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.useRealTimers()
  })

  it('renderiza a superfície operacional local com status independentes', async () => {
    renderConfiguracao()

    expect(await screen.findByText('Configuração operacional')).toBeInTheDocument()
    expect(screen.getByText(/dashboard local sem login próprio/i)).toBeInTheDocument()
    expect(screen.getByText('Conexão com sistemas externos')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Conectar PJe e SISTJWEB' })).toBeInTheDocument()
    expect(screen.getByText('Status da autenticação assistida')).toBeInTheDocument()
    expect(screen.getByText('Abrir site externamente')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Abrir PJe externamente' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Abrir SISTJWEB externamente' })).toBeInTheDocument()
    expect(screen.queryByText(/Solicitar reautenticação/i)).not.toBeInTheDocument()
    expect(screen.getByText('Diagnóstico do runtime local')).toBeInTheDocument()
    expect(screen.getByText('Tarefas pendentes')).toBeInTheDocument()
    expect(screen.getByText('Tarefas executando')).toBeInTheDocument()
    expect(screen.getByText('Sessão inativa')).toBeInTheDocument()
    expect(screen.getAllByText('Sessão ativa').length).toBeGreaterThan(0)
  })

  it('mantém visível o passo a passo da autenticação assistida', async () => {
    renderConfiguracao()

    expect(await screen.findByRole('button', { name: 'Conectar PJe e SISTJWEB' })).toBeInTheDocument()
    expect(screen.getByText('Entre no PJe.')).toBeInTheDocument()
    expect(screen.getByText('Entre no SISTJWEB.')).toBeInTheDocument()
    expect(screen.getByText('Aguarde validação automática.')).toBeInTheDocument()
  })

  it('abre PJe em nova aba quando o operador aciona a ação independente', async () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
    renderConfiguracao()

    fireEvent.click(await screen.findByRole('button', { name: 'Abrir PJe externamente' }))

    expect(openSpy).toHaveBeenCalledWith('https://pje.tjdft.jus.br/pje/login.seam', '_blank', 'noopener,noreferrer')
    openSpy.mockRestore()
  })

  it('mantém a abertura externa como ação secundária separada do fluxo principal', async () => {
    renderConfiguracao()

    expect(await screen.findByText('Abrir site externamente')).toBeInTheDocument()
    expect(screen.getByText(/Use estas ações apenas para revisão manual/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Abrir PJe' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Abrir SISTJWEB' })).not.toBeInTheDocument()
  })

  it('atualiza o status automaticamente enquanto a autenticação ainda está pendente', async () => {
    const setIntervalSpy = vi.spyOn(window, 'setInterval')
    let pollCallback: (() => void) | undefined

    setIntervalSpy.mockImplementation(
      ((handler: Parameters<typeof setInterval>[0], timeout?: number) => {
        if (timeout === 5000 && typeof handler === 'function') {
          pollCallback = handler as () => void
        }
        return 1 as unknown as ReturnType<typeof setInterval>
      }) as typeof setInterval,
    )

    renderConfiguracao()

    expect(await screen.findByText('Status da autenticação assistida')).toBeInTheDocument()
    await waitFor(() => {
      expect(mockedGet).toHaveBeenCalledTimes(2)
    })

    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 5000)
    await act(async () => {
      pollCallback?.()
    })

    await waitFor(() => {
      expect(mockedGet).toHaveBeenCalledTimes(4)
    })

    setIntervalSpy.mockRestore()
  })

  it('aciona a abertura do Navegador de sessão do SOG pelo CTA principal', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true, message: 'Chrome aberto para login em PJe e SISTJWEB.' }),
    })

    renderConfiguracao()

    fireEvent.click(await screen.findByRole('button', { name: 'Conectar PJe e SISTJWEB' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:47831/sog/session-browser/open', {
        method: 'POST',
      })
    })

    expect(await screen.findByText('Chrome aberto para login em PJe e SISTJWEB.')).toBeInTheDocument()
  })
})
