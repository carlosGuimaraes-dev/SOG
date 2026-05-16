import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

interface DemonstrativoLinkProps {
  numero: string
}

function removerMascara(numero: string): string {
  return numero.replace(/\D/g, '')
}

export default function DemonstrativoLink({ numero }: DemonstrativoLinkProps) {
  const [disponivel, setDisponivel] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false
    const url = `/dados/demonstrativos/${removerMascara(numero)}_demonstrativo.pdf`

    fetch(url, { method: 'HEAD' })
      .then((res) => {
        if (!cancelled) setDisponivel(res.ok)
      })
      .catch(() => {
        if (!cancelled) setDisponivel(false)
      })

    return () => {
      cancelled = true
    }
  }, [numero])

  const url = `/dados/demonstrativos/${removerMascara(numero)}_demonstrativo.pdf`

  return (
    <Card>
      <CardHeader>
        <CardTitle>Demonstrativo</CardTitle>
      </CardHeader>
      <CardContent>
        {disponivel === null ? (
          <p className="text-sm text-muted-foreground">Verificando disponibilidade...</p>
        ) : disponivel ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Abrir demonstrativo em PDF"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            📄 Abrir PDF
          </a>
        ) : (
          <p className="text-sm text-muted-foreground">PDF não disponível</p>
        )}
      </CardContent>
    </Card>
  )
}
