param(
  [ValidateSet("baseline", "verify")]
  [string]$Mode = "baseline",
  [string]$InstallRoot = "$env:LOCALAPPDATA\SOG"
)

$ErrorActionPreference = "Stop"

$DataDir = Join-Path $InstallRoot "dados"
$LogsDir = Join-Path $InstallRoot "logs"
$BaselineFile = Join-Path $LogsDir "upgrade-preservation-baseline.json"

function Ensure-File($Path, $Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Force $dir | Out-Null
  }
  if (-not (Test-Path $Path)) {
    Set-Content -Path $Path -Value $Content -Encoding UTF8
  }
}

function File-Fingerprint($Path) {
  if (-not (Test-Path $Path)) {
    return $null
  }
  $item = Get-Item $Path
  return [ordered]@{
    path = $Path
    exists = $true
    length = $item.Length
    sha256 = (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
  }
}

function Collect-Manifest {
  $paths = [ordered]@{
    db = Join-Path $DataDir "custas.db"
    pje_storage = Join-Path $DataDir "auth\pje_storage.json"
    sistj_storage = Join-Path $DataDir "auth\sistj_storage.json"
    pdf = Join-Path $DataDir "demonstrativos\upgrade-preservation.pdf"
    screenshot = Join-Path $DataDir "screenshots\upgrade-preservation\sentinel.png"
  }
  $files = [ordered]@{}
  foreach ($key in $paths.Keys) {
    $files[$key] = File-Fingerprint $paths[$key]
  }
  return [ordered]@{
    createdAt = (Get-Date).ToUniversalTime().ToString("o")
    installRoot = $InstallRoot
    dataDir = $DataDir
    files = $files
  }
}

if (-not (Test-Path $DataDir)) {
  New-Item -ItemType Directory -Force $DataDir | Out-Null
}
if (-not (Test-Path $LogsDir)) {
  New-Item -ItemType Directory -Force $LogsDir | Out-Null
}

if ($Mode -eq "baseline") {
  Ensure-File (Join-Path $DataDir "custas.db") "sog-upgrade-preservation-db"
  Ensure-File (Join-Path $DataDir "auth\pje_storage.json") '{"sentinel":"pje"}'
  Ensure-File (Join-Path $DataDir "auth\sistj_storage.json") '{"sentinel":"sistj"}'
  Ensure-File (Join-Path $DataDir "demonstrativos\upgrade-preservation.pdf") "sog-upgrade-preservation-pdf"
  Ensure-File (Join-Path $DataDir "screenshots\upgrade-preservation\sentinel.png") "sog-upgrade-preservation-screenshot"
  Collect-Manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $BaselineFile -Encoding UTF8
  Write-Host "Baseline de preservacao gravado: $BaselineFile"
  Write-Host "Reinstale ou atualize o SOG Desktop mantendo o mesmo usuario Windows e execute: npm run smoke:upgrade -- --Mode verify"
  exit 0
}

if (-not (Test-Path $BaselineFile)) {
  throw "Baseline nao encontrado: $BaselineFile. Execute primeiro com -Mode baseline."
}

$baseline = Get-Content $BaselineFile -Raw | ConvertFrom-Json
$current = Collect-Manifest

foreach ($entry in $baseline.files.PSObject.Properties) {
  $key = $entry.Name
  $expected = $entry.Value
  $actual = $current.files[$key]
  if (-not $expected.exists) {
    continue
  }
  if (-not $actual -or -not $actual.exists) {
    throw "Arquivo persistente desapareceu apos upgrade: $key"
  }
  if ($expected.sha256 -ne $actual.sha256) {
    throw "Arquivo persistente mudou apos upgrade: $key"
  }
}

Write-Host "Preservacao de dados OK: custas.db, PDFs, screenshots e storage_state mantidos."
