import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ErrorBoundary from './ErrorBoundary'

function ProblemChild() {
  throw new Error('falha controlada')
}

describe('ErrorBoundary', () => {
  const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

  afterEach(() => {
    consoleErrorSpy.mockClear()
  })

  it('renderiza os filhos quando não há erro', () => {
    render(
      <ErrorBoundary>
        <div>conteudo seguro</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('conteudo seguro')).toBeInTheDocument()
  })

  it('mostra fallback e permite recarregar a página após erro', () => {
    const reloadSpy = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { ...window.location, reload: reloadSpy },
      configurable: true,
    })

    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    )

    expect(screen.getByText('Algo deu errado')).toBeInTheDocument()
    expect(screen.getByText('falha controlada')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /recarregar página/i }))

    expect(reloadSpy).toHaveBeenCalledTimes(1)
  })
})
