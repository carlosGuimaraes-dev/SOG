import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import BotaoExportar from './BotaoExportar'
import api from '../../lib/api'

const addToast = vi.fn()

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

vi.mock('../../hooks/useToast', () => ({
  useToast: () => ({ addToast }),
}))

describe('BotaoExportar', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza botão de exportar', () => {
    render(<BotaoExportar />)
    expect(screen.getByRole('button', { name: /exportar histórico em csv/i })).toBeInTheDocument()
    expect(screen.getByText('📥 Exportar CSV')).toBeInTheDocument()
  })

  it('inicia download ao clicar', async () => {
    const mockGet = vi.mocked(api.get).mockResolvedValueOnce({
      data: new Blob(['csv content']),
    } as unknown as Awaited<ReturnType<typeof api.get>>)

    const createObjectURL = vi.fn(() => 'blob:url')
    window.URL.createObjectURL = createObjectURL
    const revokeObjectURL = vi.fn()
    window.URL.revokeObjectURL = revokeObjectURL
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    render(<BotaoExportar />)
    fireEvent.click(screen.getByRole('button', { name: /exportar histórico em csv/i }))

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/v1/historico/exportar', { responseType: 'blob' })
      expect(createObjectURL).toHaveBeenCalled()
    })

    clickSpy.mockRestore()
    mockGet.mockRestore()
  })

  it('usa endpoint correto', async () => {
    const mockGet = vi.mocked(api.get).mockResolvedValueOnce({
      data: new Blob(['csv content']),
    } as unknown as Awaited<ReturnType<typeof api.get>>)

    render(<BotaoExportar />)
    fireEvent.click(screen.getByRole('button', { name: /exportar histórico em csv/i }))

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/v1/historico/exportar', { responseType: 'blob' })
    })

    mockGet.mockRestore()
  })

  it('mostra loading e desabilita botão durante download', async () => {
    let resolveGet!: (value: { data: Blob }) => void
    const promise = new Promise<{ data: Blob }>((resolve) => {
      resolveGet = resolve
    })
    const mockGet = vi.mocked(api.get).mockReturnValueOnce(promise as unknown as ReturnType<typeof api.get>)
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    render(<BotaoExportar />)
    const button = screen.getByRole('button', { name: /exportar histórico em csv/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(button).toBeDisabled()
      expect(screen.getByText('⏳ Exportando...')).toBeInTheDocument()
    })

    resolveGet({ data: new Blob(['csv']) })

    await waitFor(() => {
      expect(button).not.toBeDisabled()
      expect(screen.getByText('📥 Exportar CSV')).toBeInTheDocument()
    })

    clickSpy.mockRestore()
    mockGet.mockRestore()
  })

  it('mostra toast quando a exportação falha', async () => {
    const mockGet = vi.mocked(api.get).mockRejectedValueOnce(new Error('falhou'))

    render(<BotaoExportar />)
    fireEvent.click(screen.getByRole('button', { name: /exportar histórico em csv/i }))

    await waitFor(() => {
      expect(addToast).toHaveBeenCalledWith('Erro ao exportar histórico', 'error')
      expect(screen.getByText('📥 Exportar CSV')).toBeInTheDocument()
    })

    mockGet.mockRestore()
  })
})
