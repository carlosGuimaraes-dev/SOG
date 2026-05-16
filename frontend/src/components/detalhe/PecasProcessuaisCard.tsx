import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'

interface Props {
  idsOficios?: string
  idsAlvaras?: string
  idsTraslados?: string
  idsMandados?: string
  idsCartasSentenca?: string
  idsAr?: string
  idsArmp?: string
}

export default function PecasProcessuaisCard({
  idsOficios,
  idsAlvaras,
  idsTraslados,
  idsMandados,
  idsCartasSentenca,
  idsAr,
  idsArmp,
}: Props) {
  const items = [
    ['Ofícios', idsOficios],
    ['Alvarás', idsAlvaras],
    ['Traslados', idsTraslados],
    ['Mandados', idsMandados],
    ['Cartas de Sentença', idsCartasSentenca],
    ['AR', idsAr],
    ['AR/MP', idsArmp],
  ] as const

  return (
    <Card>
      <CardHeader>
        <CardTitle>Peças Processuais (IDs PJE)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm">
        {items.map(([label, val]) => (
          <div key={label} className="flex justify-between">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-mono">{val || '-'}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
