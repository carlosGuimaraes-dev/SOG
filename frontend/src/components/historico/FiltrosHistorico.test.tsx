import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FiltrosHistorico from './FiltrosHistorico'

describe('FiltrosHistorico', () => {
  it('renderiza controles de filtro', () => {
    render(<FiltrosHistorico onChange={vi.fn()} />)
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/data/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/valor mínimo/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /limpar filtros/i })).toBeInTheDocument()
  })

  it('emite filtros ao alterar status', async () => {
    const onChange = vi.fn()
    render(<FiltrosHistorico onChange={onChange} />)

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'emitido' } })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'emitido' })
      )
    })
  })

  it('emite filtros ao alterar data', async () => {
    const onChange = vi.fn()
    render(<FiltrosHistorico onChange={onChange} />)

    fireEvent.change(screen.getByLabelText(/data/i), { target: { value: '7' } })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ data: '7' })
      )
    })
  })

  it('emite filtros ao alterar valor mínimo', async () => {
    const onChange = vi.fn()
    render(<FiltrosHistorico onChange={onChange} />)

    fireEvent.change(screen.getByLabelText(/valor mínimo/i), { target: { value: '1000' } })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ valorMinimo: '1000' })
      )
    })
  })

  it('reseta filtros ao clicar em limpar', async () => {
    const onChange = vi.fn()
    render(<FiltrosHistorico onChange={onChange} />)

    fireEvent.change(screen.getByLabelText(/status/i), { target: { value: 'rejeitado' } })
    fireEvent.change(screen.getByLabelText(/data/i), { target: { value: '30' } })
    fireEvent.change(screen.getByLabelText(/valor mínimo/i), { target: { value: '500' } })

    await waitFor(() => {
      expect(screen.getByLabelText(/status/i)).toHaveValue('rejeitado')
    })

    fireEvent.click(screen.getByRole('button', { name: /limpar filtros/i }))

    await waitFor(() => {
      expect(screen.getByLabelText(/status/i)).toHaveValue('todos')
      expect(screen.getByLabelText(/data/i)).toHaveValue('todos')
      expect(onChange).toHaveBeenCalledWith({ status: 'todos', data: 'todos', valorMinimo: '' })
    })
  })
})
