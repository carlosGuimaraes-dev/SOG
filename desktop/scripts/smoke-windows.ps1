param(
  [string]$InstallRoot = "$env:LOCALAPPDATA\SOG",
  [string]$AppResources = "",
  [string]$ComposeFile = "",
  [string]$RuntimeRoot = ""
)

$ErrorActionPreference = "Stop"

function Assert-Command($Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Comando obrigatorio nao encontrado: $Name"
  }
}

function Assert-Http($Url, $Name) {
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 500) {
      throw "$Name respondeu HTTP $($response.StatusCode)"
    }
    Write-Host "$Name OK: HTTP $($response.StatusCode)"
  } catch {
    throw "$Name offline em $Url. $($_.Exception.Message)"
  }
}

function Read-EnvValue($Path, $Name, $Default) {
  if (-not (Test-Path $Path)) {
    return $Default
  }
  foreach ($line in Get-Content $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
      continue
    }
    $index = $trimmed.IndexOf("=")
    if ($index -lt 1) {
      continue
    }
    $key = $trimmed.Substring(0, $index)
    if ($key -ne $Name) {
      continue
    }
    $value = $trimmed.Substring($index + 1).Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"') -and $value.Length -ge 2) {
      $value = $value.Substring(1, $value.Length - 2).Replace('\"', '"').Replace('\\', '\')
    }
    if ($value) {
      return $value
    }
  }
  return $Default
}

Assert-Command docker
docker version | Out-Host
docker compose version | Out-Host

if (-not $AppResources) {
  $candidateResources = @(
    (Join-Path $env:LOCALAPPDATA "Programs\SOG Desktop\resources"),
    (Join-Path $env:ProgramFiles "SOG Desktop\resources"),
    (Join-Path $PSScriptRoot "..")
  )
  foreach ($candidate in $candidateResources) {
    if ($candidate -and (Test-Path $candidate)) {
      $AppResources = (Resolve-Path $candidate).Path
      break
    }
  }
}

if (-not $RuntimeRoot) {
  $candidateRuntimeRoots = @()
  if ($AppResources) {
    $candidateRuntimeRoots += (Join-Path $AppResources "sog-runtime")
  }
  $candidateRuntimeRoots += (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
  foreach ($candidate in $candidateRuntimeRoots) {
    if ($candidate -and (Test-Path $candidate)) {
      $RuntimeRoot = (Resolve-Path $candidate).Path
      break
    }
  }
}
if (-not $ComposeFile) {
  $ComposeFile = Join-Path $RuntimeRoot "docker-compose.desktop.yml"
}

$DataDir = Join-Path $InstallRoot "dados"
$ApiEnv = Join-Path $InstallRoot "runtime\.env.api"
$AgentEnv = Join-Path $InstallRoot "runtime\.env.agente"
$ComposeEnv = Join-Path $InstallRoot "runtime\.env.compose"

if (-not (Test-Path $DataDir)) {
  throw "Pasta de dados nao encontrada: $DataDir"
}
if (-not (Test-Path $ApiEnv)) {
  throw "Configuracao da API nao encontrada: $ApiEnv"
}
if (-not (Test-Path $AgentEnv)) {
  throw "Configuracao do agente nao encontrada: $AgentEnv"
}
if (-not (Test-Path $ComposeEnv)) {
  throw "Configuracao do Docker nao encontrada: $ComposeEnv"
}
if (-not (Test-Path $ComposeFile)) {
  throw "Compose desktop nao encontrado: $ComposeFile"
}

docker compose --env-file $ComposeEnv -f $ComposeFile -p sog-desktop config --services | Out-Host

$HttpPort = Read-EnvValue $ComposeEnv "SOG_HTTP_PORT" "80"
$DashboardUrl = if ($HttpPort -eq "80") { "http://localhost" } else { "http://localhost:$HttpPort" }

Assert-Http "$DashboardUrl/" "Dashboard"
Assert-Http "$DashboardUrl/api/v1/health" "API"

$agentCandidates = @()
$browserCandidates = @()
if ($AppResources) {
  $agentCandidates += (Join-Path $AppResources "agent\sog-agent.exe")
  $browserCandidates += (Join-Path $AppResources "ms-playwright")
}
$agentCandidates += (Join-Path $PSScriptRoot "..\vendor\agent\sog-agent.exe")
$browserCandidates += (Join-Path $PSScriptRoot "..\vendor\ms-playwright")
$AgentExe = $agentCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
$BrowsersDir = $browserCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $AgentExe) {
  throw "Executavel do agente empacotado nao encontrado."
}
if (-not $BrowsersDir) {
  throw "Chromium Playwright empacotado nao encontrado."
}
Write-Host "Agente empacotado OK: $AgentExe"
Write-Host "Chromium Playwright empacotado OK: $BrowsersDir"

$TempRoot = if ($env:TEMP) { $env:TEMP } else { [System.IO.Path]::GetTempPath() }
$SmokeFile = Join-Path $TempRoot "sog-agent-smoke-$([guid]::NewGuid()).json"
$PreviousBrowsersPath = $env:PLAYWRIGHT_BROWSERS_PATH
$PreviousSmokeOutput = $env:SOG_DESKTOP_SMOKE_OUTPUT
try {
  $env:PLAYWRIGHT_BROWSERS_PATH = $BrowsersDir
  $env:SOG_DESKTOP_SMOKE_OUTPUT = $SmokeFile
  & $AgentExe --desktop-smoke
  if ($LASTEXITCODE -ne 0) {
    throw "Smoke do agente empacotado retornou codigo $LASTEXITCODE"
  }
  if (-not (Test-Path $SmokeFile)) {
    throw "Smoke do agente empacotado nao gerou evidencia"
  }
  $Smoke = Get-Content $SmokeFile -Raw | ConvertFrom-Json
  if ($Smoke.status -ne "ok" -or $Smoke.title -ne "sog-agent-smoke") {
    throw "Smoke do agente empacotado falhou"
  }
  Write-Host "Smoke do agente empacotado OK: $($Smoke.title)"
} finally {
  if ($null -eq $PreviousBrowsersPath) {
    Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
  } else {
    $env:PLAYWRIGHT_BROWSERS_PATH = $PreviousBrowsersPath
  }
  if ($null -eq $PreviousSmokeOutput) {
    Remove-Item Env:SOG_DESKTOP_SMOKE_OUTPUT -ErrorAction SilentlyContinue
  } else {
    $env:SOG_DESKTOP_SMOKE_OUTPUT = $PreviousSmokeOutput
  }
  if (Test-Path $SmokeFile) {
    Remove-Item -Force $SmokeFile
  }
}

Write-Host "Smoke Windows concluido. Valide manualmente: iniciar agente no SOG Desktop, iniciar ciclo e confirmar Chromium abrindo PJe/SISTJWEB."
