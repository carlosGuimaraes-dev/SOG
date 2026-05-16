import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import BuscaProcesso from './BuscaProcesso'

describe('BuscaProcesso', () => {
  it('renderiza input com placeholder correto', () => {
    render(<BuscaProcesso valor="" onChange={() => {}} />)
    expect(screen.getByLabelText(/buscar por número do processo/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/buscar por número do processo/i)).toBeInTheDocument()
  })

  it('dispara onChange ao digitar', () => {
    const onChange = vi.fn()
    render(<BuscaProcesso valor="" onChange={onChange} />)
    const input = screen.getByLabelText(/buscar por número do processo/i)
    fireEvent.change(input, { target: { value: '0000012' } })
    expect(onChange).toHaveBeenCalledWith('0000012')
  })

  it('exibe botão limpar quando há texto', () => {
    render(<BuscaProcesso valor="123" onChange={() => {}} />)
    expect(screen.getByLabelText(/limpar busca/i)).toBeInTheDocument()
  })

  it('não exibe botão limpar quando input está vazio', () => {
    render(<BuscaProcesso valor="" onChange={() => {}} />)
    expect(screen.queryByLabelText(/limpar busca/i)).not.toBeInTheDocument()
  })

  it('limpa valor ao clicar no botão limpar', () => {
    const onChange = vi.fn()
    render(<BuscaProcesso valor="123" onChange={onChange} />)
    fireEvent.click(screen.getByLabelText(/limpar busca/i))
    expect(onChange).toHaveBeenCalledWith('')
  })
})
