import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Paginacao from './Paginacao'

describe('Paginacao', () => {
  it('exibe texto informativo correto na primeira página', () => {
    render(<Paginacao currentPage={0} totalItems={50} itemsPerPage={20} onPageChange={vi.fn()} />)
    expect(screen.getByText('Mostrando 1-20 de 50')).toBeInTheDocument()
  })

  it('exibe texto informativo correto na última página', () => {
    render(<Paginacao currentPage={2} totalItems={50} itemsPerPage={20} onPageChange={vi.fn()} />)
    expect(screen.getByText('Mostrando 41-50 de 50')).toBeInTheDocument()
  })

  it('desabilita botão Anterior na primeira página', () => {
    render(<Paginacao currentPage={0} totalItems={50} itemsPerPage={20} onPageChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: /página anterior/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /próxima página/i })).not.toBeDisabled()
  })

  it('desabilita botão Próxima na última página', () => {
    render(<Paginacao currentPage={2} totalItems={50} itemsPerPage={20} onPageChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: /página anterior/i })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: /próxima página/i })).toBeDisabled()
  })

  it('desabilita ambos quando não há itens', () => {
    render(<Paginacao currentPage={0} totalItems={0} itemsPerPage={20} onPageChange={vi.fn()} />)
    expect(screen.getByText('Mostrando 0-0 de 0')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /página anterior/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /próxima página/i })).toBeDisabled()
  })

  it('chama onPageChange com página anterior', () => {
    const onPageChange = vi.fn()
    render(<Paginacao currentPage={1} totalItems={50} itemsPerPage={20} onPageChange={onPageChange} />)
    fireEvent.click(screen.getByRole('button', { name: /página anterior/i }))
    expect(onPageChange).toHaveBeenCalledWith(0)
  })

  it('chama onPageChange com próxima página', () => {
    const onPageChange = vi.fn()
    render(<Paginacao currentPage={0} totalItems={50} itemsPerPage={20} onPageChange={onPageChange} />)
    fireEvent.click(screen.getByRole('button', { name: /próxima página/i }))
    expect(onPageChange).toHaveBeenCalledWith(1)
  })
})
