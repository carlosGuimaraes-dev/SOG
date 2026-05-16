import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DocumentosPje from './DocumentosPje'
import type { Documento } from '../../types/processo'

const mockDocumentos: Documento[] = [
  { id: 1, processo_id: 1, doc_id: 'doc-1', tipo: 'Petição Inicial', data_assinatura: '2024-01-15T10:00:00', nome: 'Petição.pdf' },
  { id: 2, processo_id: 1, doc_id: 'doc-2', tipo: 'Sentença', nome: 'Sentença.pdf' },
]

describe('DocumentosPje', () => {
  it('renderiza estado vazio quando não há documentos', () => {
    render(<DocumentosPje documentos={[]} />)
    expect(screen.getByText('Nenhum documento extraído')).toBeInTheDocument()
  })

  it('renderiza estado vazio quando documentos é undefined', () => {
    render(<DocumentosPje />)
    expect(screen.getByText('Nenhum documento extraído')).toBeInTheDocument()
  })

  it('renderiza tabela com todos os documentos', () => {
    render(<DocumentosPje documentos={mockDocumentos} />)
    expect(screen.getByText('Petição Inicial')).toBeInTheDocument()
    expect(screen.getByText('Sentença')).toBeInTheDocument()
    expect(screen.getByText('Petição.pdf')).toBeInTheDocument()
    expect(screen.getByText('Sentença.pdf')).toBeInTheDocument()
  })

  it('formata data de assinatura em pt-BR', () => {
    render(<DocumentosPje documentos={mockDocumentos} />)
    expect(screen.getByText('15/01/2024')).toBeInTheDocument()
  })

  it('exibe "-" quando data_assinatura está ausente', () => {
    render(<DocumentosPje documentos={mockDocumentos} />)
    const linhas = screen.getAllByRole('row')
    const linhaSentenca = linhas.find((row) => row.textContent?.includes('Sentença'))
    expect(linhaSentenca).toHaveTextContent('-')
  })

  it('exibe "-" quando nome está ausente', () => {
    const docsSemNome: Documento[] = [
      { id: 3, processo_id: 1, doc_id: 'doc-3', tipo: 'Despacho' },
    ]
    render(<DocumentosPje documentos={docsSemNome} />)
    const linhas = screen.getAllByRole('row')
    const linhaDespacho = linhas.find((row) => row.textContent?.includes('Despacho'))
    expect(linhaDespacho).toHaveTextContent('-')
  })
})
