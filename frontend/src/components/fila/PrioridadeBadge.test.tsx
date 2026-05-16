import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PrioridadeBadge from './PrioridadeBadge'

describe('PrioridadeBadge', () => {
  it('exibe badge Urgente quando há tentativas e erro_msg', () => {
    const processo = {
      id: 1,
      numero: '0000012-75.2023.8.07.0001',
      status: 'aguardando_aprovacao',
      criado_em: new Date().toISOString(),
      tentativas: 3,
      erro_msg: 'Falha na conexão',
    }
    render(<PrioridadeBadge processo={processo} />)
    expect(screen.getByText('Urgente')).toBeInTheDocument()
  })

  it('exibe badge Alto Valor quando valor > R$ 50.000', () => {
    const processo = {
      id: 1,
      numero: '0000012-75.2023.8.07.0001',
      status: 'aguardando_aprovacao',
      criado_em: new Date().toISOString(),
      valor_total_recolher: 'R$ 75.000,00',
    }
    render(<PrioridadeBadge processo={processo} />)
    expect(screen.getByText('Alto Valor')).toBeInTheDocument()
  })

  it('exibe badge Antigo quando processo tem mais de 7 dias', () => {
    const dataAntiga = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
    const processo = {
      id: 1,
      numero: '0000012-75.2023.8.07.0001',
      status: 'aguardando_aprovacao',
      criado_em: dataAntiga,
    }
    render(<PrioridadeBadge processo={processo} />)
    expect(screen.getByText('Antigo')).toBeInTheDocument()
  })

  it('não exibe badges quando não há critérios', () => {
    const processo = {
      id: 1,
      numero: '0000012-75.2023.8.07.0001',
      status: 'aguardando_aprovacao',
      criado_em: new Date().toISOString(),
      tentativas: 0,
      valor_total_recolher: 'R$ 1.000,00',
    }
    render(<PrioridadeBadge processo={processo} />)
    expect(screen.queryByText('Urgente')).not.toBeInTheDocument()
    expect(screen.queryByText('Alto Valor')).not.toBeInTheDocument()
    expect(screen.queryByText('Antigo')).not.toBeInTheDocument()
  })

  it('exibe múltiplos badges quando vários critérios são atendidos', () => {
    const dataAntiga = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
    const processo = {
      id: 1,
      numero: '0000012-75.2023.8.07.0001',
      status: 'aguardando_aprovacao',
      criado_em: dataAntiga,
      tentativas: 2,
      erro_msg: 'Erro',
      valor_total_recolher: 'R$ 60.000,00',
    }
    render(<PrioridadeBadge processo={processo} />)
    expect(screen.getByText('Urgente')).toBeInTheDocument()
    expect(screen.getByText('Alto Valor')).toBeInTheDocument()
    expect(screen.getByText('Antigo')).toBeInTheDocument()
  })
})
