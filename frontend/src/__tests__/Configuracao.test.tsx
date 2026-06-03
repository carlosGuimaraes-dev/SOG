import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import Configuracao from '../pages/Configuracao'
import { ENDPOINTS } from '../lib/endpoints'

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
const mockedPost = vi.mocked(api.post)

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
    mockApi()
  })

  it('renderiza a superfície operacional local com status independentes', async () => {
    renderConfiguracao()

    expect(await screen.findByText('Configuração operacional')).toBeInTheDocument()
    expect(screen.getByText(/dashboard local sem login próprio/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Abrir PJe' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Abrir SISTJWEB' })).toBeInTheDocument()
    expect(screen.getAllByText(/Solicitar reautenticação/i)).toHaveLength(2)
    expect(screen.getByText('Diagnóstico do runtime local')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('Sessão inativa')).toBeInTheDocument()
    expect(screen.getAllByText('Sessão ativa').length).toBeGreaterThan(0)
  })

  it('abre PJe em nova aba quando o operador aciona a ação independente', async () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
    renderConfiguracao()

    fireEvent.click(await screen.findByRole('button', { name: 'Abrir PJe' }))

    expect(openSpy).toHaveBeenCalledWith('https://pje.tjdft.jus.br/pje/login.seam', '_blank', 'noopener,noreferrer')
    openSpy.mockRestore()
  })

  it('solicita reautenticação do SISTJWEB usando a rota real', async () => {
    mockedPost.mockResolvedValue({ data: { message: 'ok' } })
    renderConfiguracao()

    const botoes = await screen.findAllByRole('button', { name: 'Solicitar reautenticação' })
    fireEvent.click(botoes[1])

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith('/sistj/reautenticar')
    })
  })
})
