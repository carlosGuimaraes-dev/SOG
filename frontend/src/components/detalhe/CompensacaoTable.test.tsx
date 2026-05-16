import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import CompensacaoTable from './CompensacaoTable'
import type { Compensacao } from '../../types/processo'

const mockCompensacoes: Compensacao[] = [
  { data: '2024-01-15', valor: 'R$ 1.000,00', numero_guia: '12345' },
  { data: '2024-02-20', valor: 'R$ 500,00', numeroGuia: '67890' },
]

describe('CompensacaoTable', () => {
  it('renderiza "Nenhuma compensação" quando não há itens', () => {
    render(<CompensacaoTable items={[]} />)
    expect(screen.getByText('Nenhuma compensação')).toBeInTheDocument()
  })

  it('renderiza "Nenhuma compensação" quando items é undefined', () => {
    render(<CompensacaoTable />)
    expect(screen.getByText('Nenhuma compensação')).toBeInTheDocument()
  })

  it('renderiza tabela com todas as compensações', () => {
    render(<CompensacaoTable items={mockCompensacoes} />)
    expect(screen.getByText('R$ 1.000,00')).toBeInTheDocument()
    expect(screen.getByText('R$ 500,00')).toBeInTheDocument()
    expect(screen.getByText('12345')).toBeInTheDocument()
    expect(screen.getByText('67890')).toBeInTheDocument()
  })

  it('trata campo numero_guia como fallback para numeroGuia', () => {
    render(<CompensacaoTable items={mockCompensacoes} />)
    expect(screen.getByText('12345')).toBeInTheDocument()
    expect(screen.getByText('67890')).toBeInTheDocument()
  })

  it('exibe "-" quando campos estão ausentes', () => {
    const incompleto: Compensacao[] = [{ data: undefined, valor: undefined, numero_guia: undefined }]
    render(<CompensacaoTable items={incompleto} />)
    const linhas = screen.getAllByRole('row')
    const linhaDados = linhas.find((row) => row.classList.contains('border-b') && row.textContent?.includes('-'))
    expect(linhaDados).toBeDefined()
  })
})
