import { useState } from 'react'
import Input from '../ui/Input'

interface Props {
  valor: string
  onChange: (valor: string) => void
}

export default function BuscaProcesso({ valor, onChange }: Props) {
  const [busca, setBusca] = useState(valor)

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value
    setBusca(v)
    onChange(v)
  }

  function limpar() {
    setBusca('')
    onChange('')
  }

  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </span>
      <Input
        type="text"
        placeholder="Buscar por número do processo..."
        value={busca}
        onChange={handleChange}
        className="pl-10 pr-10"
        aria-label="Buscar por número do processo"
      />
      {busca && (
        <button
          type="button"
          onClick={limpar}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          aria-label="Limpar busca"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      )}
    </div>
  )
}
