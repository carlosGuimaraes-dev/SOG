import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ResumoPreenchimento from './ResumoPreenchimento'
import type { DadosProcesso } from '../../types/processo'

const mockCompleto: DadosProcesso = {
  sucumbente_nome: 'João da Silva',
  ids_oficios: '1,2,3',
  ids_alvaras: '4',
  ids_traslados: '5,6',
  ids_mandados: '',
  ids_cartas_sentenca: '7',
  ids_ar: '8,9,10',
  ids_armp: '',
  outros_itens: [
    { item_guia: 'Item 1', quantidade: '2' },
    { item_guia: 'Item 2', quantidade: '1' },
  ],
  valor_total_recolher: 'R$ 1.234,56',
}

const mockIncompleto: DadosProcesso = {
  ids_oficios: '',
  ids_alvaras: '',
  ids_traslados: '',
  ids_mandados: '',
  ids_cartas_sentenca: '',
  ids_ar: '',
  ids_armp: '',
}

describe('ResumoPreenchimento', () => {
  it('exibe todos os 4 campos com dados completos', () => {
    render(<ResumoPreenchimento dados={mockCompleto} />)
    expect(screen.getByText('João da Silva')).toBeInTheDocument()
    expect(screen.getByText('10 peças')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('R$ 1.234,56')).toBeInTheDocument()
  })

  it('trata dados ausentes corretamente', () => {
    render(<ResumoPreenchimento dados={mockIncompleto} />)
    expect(screen.getByText('Não identificado')).toBeInTheDocument()
    expect(screen.getByText('Nenhum')).toBeInTheDocument()
    expect(screen.getAllByText('-').length).toBeGreaterThanOrEqual(1)
  })

  it('conta corretamente peças com múltiplos IDs', () => {
    render(<ResumoPreenchimento dados={mockCompleto} />)
    // 3 ofícios + 1 alvará + 2 traslados + 0 mandados + 1 carta sentença + 3 AR + 0 ARMP = 10
    expect(screen.getByText('10 peças')).toBeInTheDocument()
  })
})
