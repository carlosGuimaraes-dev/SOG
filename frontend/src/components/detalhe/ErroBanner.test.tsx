import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErroBanner from './ErroBanner'

describe('ErroBanner', () => {
  it('renderiza título e mensagem de erro', () => {
    render(<ErroBanner mensagem="Falha na conexão com PJE" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Erro na execução')).toBeInTheDocument()
    expect(screen.getByText('Falha na conexão com PJE')).toBeInTheDocument()
  })
})
