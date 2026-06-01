param(
  [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

$DesktopRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RepoRoot = Resolve-Path (Join-Path $DesktopRoot "..")
$VendorRoot = Join-Path $DesktopRoot "vendor"
$VenvPath = Join-Path $VendorRoot "python-build"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$AgentDist = Join-Path $VendorRoot "agent"
$BrowsersPath = Join-Path $VendorRoot "ms-playwright"
$PyInstallerBuild = Join-Path $VendorRoot "pyinstaller-build"
$PyInstallerSpec = Join-Path $VendorRoot "pyinstaller-spec"

foreach ($PathToClean in @($VenvPath, $AgentDist, $BrowsersPath, $PyInstallerBuild, $PyInstallerSpec)) {
  if (Test-Path $PathToClean) {
    Remove-Item -Recurse -Force $PathToClean
  }
}

New-Item -ItemType Directory -Force $VendorRoot | Out-Null
New-Item -ItemType Directory -Force $AgentDist | Out-Null
New-Item -ItemType Directory -Force $BrowsersPath | Out-Null
& $PythonCommand -m venv $VenvPath
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $RepoRoot "agente\requirements.txt")
& $PythonExe -m pip install -e (Join-Path $RepoRoot "shared")
& $PythonExe -m pip install pyinstaller
$env:PLAYWRIGHT_BROWSERS_PATH = $BrowsersPath
& $PythonExe -m playwright install chromium
& $PythonExe -m PyInstaller `
  --name sog-agent `
  --onefile `
  --noconsole `
  --clean `
  --paths (Join-Path $RepoRoot "agente\src") `
  --paths (Join-Path $RepoRoot "shared") `
  --collect-all playwright `
  --collect-all sog_shared `
  --hidden-import sog_shared.db `
  --distpath $AgentDist `
  --workpath $PyInstallerBuild `
  --specpath $PyInstallerSpec `
  (Join-Path $RepoRoot "agente\src\servico.py")

& $PythonExe --version
& $PythonExe -m playwright --version
if (-not (Test-Path (Join-Path $AgentDist "sog-agent.exe"))) {
  throw "PyInstaller nao gerou sog-agent.exe"
}

$SmokeFile = Join-Path $VendorRoot "agent-smoke.json"
if (Test-Path $SmokeFile) {
  Remove-Item -Force $SmokeFile
}
$env:SOG_DESKTOP_SMOKE_OUTPUT = $SmokeFile
$smokeProcess = Start-Process `
  -FilePath (Join-Path $AgentDist "sog-agent.exe") `
  -ArgumentList @("--desktop-smoke", "--desktop-smoke-output", $SmokeFile) `
  -Wait `
  -PassThru
if ($smokeProcess.ExitCode -ne 0) {
  throw "Smoke do sog-agent.exe retornou codigo $($smokeProcess.ExitCode)"
}
if (-not (Test-Path $SmokeFile)) {
  throw "Smoke do sog-agent.exe nao gerou evidencia"
}
$Smoke = Get-Content $SmokeFile -Raw | ConvertFrom-Json
if ($Smoke.status -ne "ok" -or $Smoke.title -ne "sog-agent-smoke") {
  throw "Smoke do sog-agent.exe falhou"
}
Remove-Item -Force $SmokeFile
