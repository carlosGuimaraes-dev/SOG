import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import CicloAtual from '../pages/CicloAtual'
import { ENDPOINTS } from '../lib/endpoints'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

vi.mock('../components/agente/AgenteStatusBar', () => ({
  default: () => <div>Status do agente</div>,
}))

import api from '../lib/api'

const mockedGet = vi.mocked(api.get)

const dashboardResumo = {
  agente_online: true,
  agente_status: 'executando',
  tarefas_pendentes: 4,
  tarefas_executando: 2,
  pje: { logado: true, mensagem: 'Sessão ativa' },
  sistj: { logado: false, mensagem: 'Sessão pendente' },
}

function mockApi({
  ciclo,
  aguardando = [],
  manual = [],
}: {
  ciclo: Record<string, unknown> | null
  aguardando?: Array<Record<string, unknown>>
  manual?: Array<Record<string, unknown>>
}) {
  mockedGet.mockImplementation((url: string) => {
    if (url === ENDPOINTS.AGENTE_CICLO_ATUAL) {
      return Promise.resolve({ data: ciclo })
    }

    if (url === ENDPOINTS.PROCESSOS) {
      return Promise.resolve({
        data: {
          aguardando_aprovacao: aguardando,
          pendente_manual: manual,
        },
      })
    }

    if (url === ENDPOINTS.DASHBOARD_SESSOES) {
      return Promise.resolve({ data: dashboardResumo })
    }

    return Promise.resolve({ data: null })
  })
}

function renderCicloAtual() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <CicloAtual />
      </ToastProvider>
    </BrowserRouter>,
  )
}

describe('CicloAtual', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza tabela do ciclo com ações contextuais por status', async () => {
    mockApi({
      ciclo: {
        uuid: 'ciclo-1',
        rotulo: 'Ciclo 2026-05-31 10:00',
        status: 'executando',
        total_membros: 3,
        total_novos: 2,
        total_rearmados: 1,
        total_concluidos: 1,
        total_erros: 1,
        membros: [
          {
            id: 10,
            processo_id: 1,
            numero: '0000012-75.2023.8.07.0001',
            origem: 'novo_pje',
            status_snapshot: 'pendente',
            status_atual: 'aguardando_aprovacao',
            criado_em: '2026-05-31T10:00:00',
          },
          {
            id: 11,
            processo_id: 2,
            numero: '0000023-12.2023.8.07.0002',
            origem: 'rearmado',
            status_snapshot: 'erro',
            status_atual: 'erro',
            criado_em: '2026-05-31T10:01:00',
          },
          {
            id: 12,
            processo_id: 3,
            numero: '0000034-11.2023.8.07.0003',
            origem: 'novo_pje',
            status_snapshot: 'pendente',
            status_atual: 'pendente_manual',
            criado_em: '2026-05-31T10:02:00',
          },
        ],
      },
      aguardando: [
        {
          id: 1,
          numero: '0000012-75.2023.8.07.0001',
          status: 'aguardando_aprovacao',
          criado_em: '2026-05-31T10:00:00',
          valor_total_recolher: 'R$ 1.500,00',
        },
      ],
      manual: [
        {
          id: 3,
          numero: '0000034-11.2023.8.07.0003',
          status: 'pendente_manual',
          criado_em: '2026-05-31T10:02:00',
          reprocessar_solicitado_em: '2026-05-31T11:00:00',
        },
      ],
    })

    renderCicloAtual()

    await waitFor(() => {
      expect(screen.getByText('Tabela operacional do ciclo')).toBeInTheDocument()
    })

    expect(screen.getByRole('columnheader', { name: 'Processo' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Status' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Etapa atual' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Guia' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Tempo' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Ação' })).toBeInTheDocument()

    expect(screen.getByText('0000012-75.2023.8.07.0001')).toBeInTheDocument()
    expect(screen.getByText('Aguardando aprovação')).toBeInTheDocument()
    expect(screen.getByText('Conferência final do operador')).toBeInTheDocument()
    expect(screen.getByText('Guia pronta: R$ 1.500,00')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /revisar aprovação do processo 0000012-75.2023.8.07.0001/i })).toHaveAttribute('href', '/detalhe/1')

    expect(screen.getByText('0000023-12.2023.8.07.0002')).toBeInTheDocument()
    expect(screen.getByText('Erro')).toBeInTheDocument()
    expect(screen.getByText('Falha operacional no ciclo')).toBeInTheDocument()
    expect(screen.getByText('Guia bloqueada por falha operacional')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /solicitar reprocessamento do processo 0000023-12.2023.8.07.0002/i })).toHaveAttribute('href', '/detalhe/2')

    expect(screen.getByText('0000034-11.2023.8.07.0003')).toBeInTheDocument()
    expect(screen.getByText('Pendência manual')).toBeInTheDocument()
    expect(screen.getByText('Aguardando próximo ciclo')).toBeInTheDocument()
    expect(screen.getByText('Reprocessamento já solicitado')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reprocessamento solicitado' })).toBeDisabled()
  })

  it('exibe alerta quando não existe ciclo atual publicado', async () => {
    mockApi({
      ciclo: null,
    })

    renderCicloAtual()

    await waitFor(() => {
      expect(screen.getByText(/nenhum ciclo ativo no momento/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/use a barra do agente para iniciar ou retomar um ciclo/i)).toBeInTheDocument()
    expect(screen.getByText(/nenhum processo vinculado ao ciclo atual/i)).toBeInTheDocument()
  })
})
