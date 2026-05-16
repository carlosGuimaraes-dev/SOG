import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { Log } from '../../types/processo'

interface Props {
  logs?: Log[]
}

const statusConfig = {
  ok: { bg: 'bg-green-500', container: '' },
  erro: { bg: 'bg-destructive', container: 'bg-destructive/10 text-destructive' },
  aviso: { bg: 'bg-yellow-500', container: '' },
}

export default function LogsTimeline({ logs }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Logs de Execução</CardTitle>
      </CardHeader>
      <CardContent>
        {(!logs || logs.length === 0) ? (
          <p className="text-sm text-muted-foreground">Nenhum log registrado</p>
        ) : (
          <div className="relative border-l-2 border-border pl-4 space-y-4">
            {[...logs]
              .sort((a, b) => new Date(b.criado_em).getTime() - new Date(a.criado_em).getTime())
              .map((log) => {
                const config = statusConfig[log.status]
                return (
                  <div
                    key={log.id}
                    className={`relative rounded-md p-3 ${config.container}`}
                  >
                    <span
                      className={`absolute -left-[21px] top-4 h-3 w-3 rounded-full ${config.bg} ring-2 ring-background`}
                      aria-hidden="true"
                    />
                    <div className="flex flex-col gap-1">
                      <span className="font-semibold text-sm">{log.etapa}</span>
                      {log.mensagem && (
                        <span className="text-sm">{log.mensagem}</span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {new Date(log.criado_em).toLocaleString('pt-BR')}
                      </span>
                    </div>
                  </div>
                )
              })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
