import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AvisosAlert from './AvisosAlert'

describe('AvisosAlert', () => {
  it('não renderiza quando não há avisos', () => {
    const { container } = render(
      <AvisosAlert areaDireito="civel" suspensao={false} sucumbenteNome="João" valorTotalRecolher="R$ 10.000,00" />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renderiza aviso de área não mapeada', () => {
    render(<AvisosAlert areaDireito="default" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/Área não mapeada/i)).toBeInTheDocument()
  })

  it('renderiza aviso de suspensão', () => {
    render(<AvisosAlert suspensao={true} />)
    expect(screen.getByText(/Suspensão de exigibilidade/i)).toBeInTheDocument()
  })

  it('renderiza aviso de sucumbente não identificado', () => {
    render(<AvisosAlert sucumbenteNome="" />)
    expect(screen.getByText(/Sucumbente não identificado/i)).toBeInTheDocument()
  })

  it('renderiza aviso de valor alto quando > R$ 50.000', () => {
    render(<AvisosAlert valorTotalRecolher="R$ 75.000,00" />)
    expect(screen.getByText(/Valor total muito alto/i)).toBeInTheDocument()
  })

  it('não renderiza aviso de valor alto quando <= R$ 50.000', () => {
    const { container } = render(<AvisosAlert areaDireito="civel" suspensao={false} sucumbenteNome="João" valorTotalRecolher="R$ 50.000,00" />)
    expect(container.firstChild).toBeNull()
  })

  it('não renderiza aviso de valor alto quando valor é undefined', () => {
    const { container } = render(<AvisosAlert areaDireito="civel" suspensao={false} sucumbenteNome="João" />)
    expect(container.firstChild).toBeNull()
  })

  it('renderiza múltiplos avisos simultaneamente', () => {
    render(
      <AvisosAlert
        areaDireito="default"
        suspensao={true}
        sucumbenteNome=""
        valorTotalRecolher="R$ 100.000,00"
      />
    )
    expect(screen.getByText(/Área não mapeada/i)).toBeInTheDocument()
    expect(screen.getByText(/Suspensão de exigibilidade/i)).toBeInTheDocument()
    expect(screen.getByText(/Sucumbente não identificado/i)).toBeInTheDocument()
    expect(screen.getByText(/Valor total muito alto/i)).toBeInTheDocument()
  })

  it('funciona com formato sem R$', () => {
    render(<AvisosAlert valorTotalRecolher="75000,00" />)
    expect(screen.getByText(/Valor total muito alto/i)).toBeInTheDocument()
  })
})
