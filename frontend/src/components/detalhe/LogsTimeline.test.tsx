import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LogsTimeline from './LogsTimeline'
import type { Log } from '../../types/processo'

const mockLogs: Log[] = [
  { id: 1, processo_id: 1, etapa: 'Login PJE', status: 'ok', mensagem: 'Autenticado com sucesso', criado_em: '2024-01-15T10:00:00' },
  { id: 2, processo_id: 1, etapa: 'Extração de dados', status: 'erro', mensagem: 'Timeout ao carregar página', criado_em: '2024-01-15T10:05:00' },
  { id: 3, processo_id: 1, etapa: 'Tentativa retry', status: 'aviso', mensagem: 'Aguardando disponibilidade', criado_em: '2024-01-15T10:03:00' },
]

describe('LogsTimeline', () => {
  it('renderiza estado vazio quando não há logs', () => {
    render(<LogsTimeline logs={[]} />)
    expect(screen.getByText('Nenhum log registrado')).toBeInTheDocument()
  })

  it('renderiza estado vazio quando logs é undefined', () => {
    render(<LogsTimeline />)
    expect(screen.getByText('Nenhum log registrado')).toBeInTheDocument()
  })

  it('renderiza todos os logs na timeline', () => {
    render(<LogsTimeline logs={mockLogs} />)
    expect(screen.getByText('Login PJE')).toBeInTheDocument()
    expect(screen.getByText('Extração de dados')).toBeInTheDocument()
    expect(screen.getByText('Tentativa retry')).toBeInTheDocument()
  })

  it('ordena logs do mais recente para o mais antigo', () => {
    render(<LogsTimeline logs={mockLogs} />)
    const items = screen.getAllByText(/Login PJE|Extração de dados|Tentativa retry/)
    expect(items[0]).toHaveTextContent('Extração de dados')
    expect(items[1]).toHaveTextContent('Tentativa retry')
    expect(items[2]).toHaveTextContent('Login PJE')
  })

  it('destaca logs com status erro', () => {
    render(<LogsTimeline logs={mockLogs} />)
    const erroLog = screen.getByText('Timeout ao carregar página').closest('div.relative')
    expect(erroLog).toHaveClass('bg-destructive/10')
    expect(erroLog).toHaveClass('text-destructive')
  })

  it('exibe timestamps formatados em pt-BR', () => {
    render(<LogsTimeline logs={mockLogs} />)
    expect(screen.getByText('15/01/2024, 10:05:00')).toBeInTheDocument()
  })
})
