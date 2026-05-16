import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LinkPje from './LinkPje'

describe('LinkPje', () => {
  it('renderiza link com URL correta', () => {
    render(<LinkPje numero="0000012-75.2023.8.07.0001" />)
    const link = screen.getByRole('link', { name: /abrir processo no pje/i })
    expect(link).toHaveAttribute(
      'href',
      'https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso=0000012-75.2023.8.07.0001'
    )
  })

  it('possui target="_blank" e rel="noopener noreferrer"', () => {
    render(<LinkPje numero="0000012-75.2023.8.07.0001" />)
    const link = screen.getByRole('link', { name: /abrir processo no pje/i })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('codifica número do processo na URL', () => {
    render(<LinkPje numero="0000012-75.2023.8.07.0001" />)
    const link = screen.getByRole('link', { name: /abrir processo no pje/i })
    expect(link.getAttribute('href')).toContain(encodeURIComponent('0000012-75.2023.8.07.0001'))
  })
})
