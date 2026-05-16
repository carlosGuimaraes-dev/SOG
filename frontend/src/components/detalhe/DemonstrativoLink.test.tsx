import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import DemonstrativoLink from './DemonstrativoLink'

describe('DemonstrativoLink', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('exibe estado de verificação inicial', () => {
    vi.mocked(global.fetch).mockReturnValueOnce(new Promise(() => {}))
    render(<DemonstrativoLink numero="0000012-75.2023.8.07.0001" />)
    expect(screen.getByText(/verificando disponibilidade/i)).toBeInTheDocument()
  })

  it('exibe link quando PDF está disponível', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({ ok: true } as Response)
    render(<DemonstrativoLink numero="0000012-75.2023.8.07.0001" />)

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /abrir demonstrativo em pdf/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
      expect(link.getAttribute('href')).toContain('00000127520238070001')
      expect(link.getAttribute('href')).toContain('_demonstrativo.pdf')
    })
  })

  it('exibe indisponibilidade quando PDF não existe', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({ ok: false } as Response)
    render(<DemonstrativoLink numero="0000012-75.2023.8.07.0001" />)

    await waitFor(() => {
      expect(screen.getByText(/pdf não disponível/i)).toBeInTheDocument()
    })
  })

  it('remove máscara do número na URL', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({ ok: true } as Response)
    render(<DemonstrativoLink numero="1234567-89.2023.8.07.0001" />)

    await waitFor(() => {
      const link = screen.getByRole('link')
      expect(link.getAttribute('href')).toContain('12345678920238070001')
    })
  })
})
