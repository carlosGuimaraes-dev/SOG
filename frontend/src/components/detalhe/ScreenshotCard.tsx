import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { ENDPOINTS } from '../../lib/endpoints'

interface Props {
  processoId: number
  screenshotPath?: string
}

export default function ScreenshotCard({ processoId, screenshotPath }: Props) {
  const [error, setError] = useState(false)

  if (!screenshotPath) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Screenshot SISTJWEB</CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex h-48 w-full items-center justify-center rounded-lg border bg-muted text-sm text-muted-foreground">
            Screenshot não disponível
          </div>
        ) : (
          <img
            src={ENDPOINTS.SCREENSHOT(processoId)}
            alt="Screenshot do sistema SISTJWEB"
            className="w-full rounded-lg border"
            onError={() => setError(true)}
          />
        )}
      </CardContent>
    </Card>
  )
}
