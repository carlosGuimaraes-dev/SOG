import { useState, useCallback, useEffect } from 'react'
import Button from '../ui/Button'
import Input from '../ui/Input'

export interface FiltrosState {
  status: string
  data: string
  valorMinimo: string
}

interface FiltrosHistoricoProps {
  onChange: (filtros: FiltrosState) => void
}

const STATUS_OPTIONS = [
  { value: 'todos', label: 'Todos' },
  { value: 'emitido', label: 'Emitido' },
  { value: 'rejeitado', label: 'Rejeitado' },
]

const DATA_OPTIONS = [
  { value: 'todos', label: 'Todos' },
  { value: '7', label: 'Últimos 7 dias' },
  { value: '30', label: 'Últimos 30 dias' },
  { value: '90', label: 'Últimos 90 dias' },
]

export default function FiltrosHistorico({ onChange }: FiltrosHistoricoProps) {
  const [status, setStatus] = useState('todos')
  const [data, setData] = useState('todos')
  const [valorMinimo, setValorMinimo] = useState('')

  const emitir = useCallback(() => {
    onChange({ status, data, valorMinimo })
  }, [status, data, valorMinimo, onChange])

  useEffect(() => {
    emitir()
  }, [emitir])

  function limpar() {
    setStatus('todos')
    setData('todos')
    setValorMinimo('')
  }

  return (
    <div className="flex flex-wrap items-end gap-4" role="search" aria-label="Filtros do histórico">
      <div className="flex flex-col gap-1">
        <label htmlFor="filtro-status" className="text-sm font-medium">
          Status
        </label>
        <select
          id="filtro-status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="flex h-10 w-40 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="filtro-data" className="text-sm font-medium">
          Data
        </label>
        <select
          id="filtro-data"
          value={data}
          onChange={(e) => setData(e.target.value)}
          className="flex h-10 w-48 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {DATA_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="filtro-valor" className="text-sm font-medium">
          Valor mínimo (R$)
        </label>
        <Input
          id="filtro-valor"
          type="number"
          min={0}
          step="0.01"
          value={valorMinimo}
          onChange={(e) => setValorMinimo(e.target.value)}
          placeholder="0,00"
          className="w-40"
        />
      </div>

      <Button variant="ghost" onClick={limpar} aria-label="Limpar filtros">
        Limpar filtros
      </Button>
    </div>
  )
}
