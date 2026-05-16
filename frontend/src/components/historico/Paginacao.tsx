import Button from '../ui/Button'

interface PaginacaoProps {
  currentPage: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
}

export default function Paginacao({
  currentPage,
  totalItems,
  itemsPerPage,
  onPageChange,
}: PaginacaoProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage)
  const startItem = totalItems === 0 ? 0 : currentPage * itemsPerPage + 1
  const endItem = Math.min((currentPage + 1) * itemsPerPage, totalItems)

  const hasPrevious = currentPage > 0
  const hasNext = currentPage < totalPages - 1

  return (
    <div className="flex items-center justify-between py-4" aria-label="Paginação">
      <span className="text-sm text-muted-foreground">
        Mostrando {startItem}-{endItem} de {totalItems}
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrevious}
          aria-label="Página anterior"
        >
          Anterior
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext}
          aria-label="Próxima página"
        >
          Próxima
        </Button>
      </div>
    </div>
  )
}
