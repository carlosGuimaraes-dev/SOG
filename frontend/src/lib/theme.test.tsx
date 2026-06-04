import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ThemeToggle from '../components/ThemeToggle'
import { ThemeProvider } from './theme'

function renderThemeToggle() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  )
}

describe('ThemeProvider', () => {
  const originalMatchMedia = window.matchMedia

  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    window.matchMedia = originalMatchMedia
    document.documentElement.className = ''
  })

  it('prioriza o tema salvo e alterna para claro ao clicar', () => {
    localStorage.setItem('sog-theme', 'dark')

    renderThemeToggle()

    const button = screen.getByRole('button', { name: /alternar para tema claro/i })
    expect(document.documentElement).toHaveClass('dark')

    fireEvent.click(button)

    expect(screen.getByRole('button', { name: /alternar para tema escuro/i })).toBeInTheDocument()
    expect(document.documentElement).toHaveClass('light')
    expect(localStorage.getItem('sog-theme')).toBe('light')
  })

  it('usa preferência do sistema quando não há tema salvo', () => {
    window.matchMedia = vi.fn().mockReturnValue({ matches: true }) as typeof window.matchMedia

    renderThemeToggle()

    expect(screen.getByRole('button', { name: /alternar para tema claro/i })).toBeInTheDocument()
    expect(document.documentElement).toHaveClass('dark')
    expect(localStorage.getItem('sog-theme')).toBe('dark')
  })
})
