const fs = require('node:fs')
const path = require('node:path')

const desktopRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(desktopRoot, '..')

function read(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), 'utf8')
}

function exists(relativePath) {
  return fs.existsSync(path.join(repoRoot, relativePath))
}

function pass(name, evidence) {
  return { name, status: 'ok', evidence }
}

function external(name, evidence) {
  return { name, status: 'external', evidence }
}

function check(name, condition, evidence) {
  if (!condition) {
    throw new Error(`Plano incompleto: ${name}`)
  }
  return pass(name, evidence)
}

const pkg = JSON.parse(read('desktop/package.json'))
const main = read('desktop/main.js')
const preload = read('desktop/preload.js')
const renderer = read('desktop/renderer/app.js')
const html = read('desktop/renderer/index.html')
const compose = read('docker-compose.desktop.yml')
const prepare = read('desktop/scripts/prepare-python-runtime.ps1')
const smoke = read('desktop/scripts/smoke-windows.ps1')
const smokeUpgrade = read('desktop/scripts/smoke-upgrade-preservation.ps1')
const authManager = read('agente/src/modulos/auth_manager.py')
const dashboard = read('frontend/src/components/agente/AgenteStatusBar.tsx')
const workflowWindows = read('.github/workflows/sog-desktop-windows.yml')
const workflowImages = read('.github/workflows/sog-desktop-images.yml')
const docs = read('docs/instalador-desktop.md')

const results = [
  check('Electron gráfico SOG Desktop', exists('desktop/main.js') && html.includes('SOG Desktop'), 'desktop/main.js + renderer/index.html'),
  check('Wizard de configuração sem terminal', html.includes('config-form') && html.includes('choose-data-dir'), 'desktop/renderer/index.html'),
  check('Detecção e guia Docker Desktop', main.includes('checkDocker') && main.includes('DOCKER_DESKTOP_URL') && main.includes('openDockerDesktop'), 'desktop/main.js'),
  check('Start/stop/restart da stack Docker', main.includes('startStack') && main.includes('stopStack') && main.includes('restartStack'), 'desktop/main.js'),
  check('Dashboard abre automaticamente após subir/reiniciar', main.includes('Dashboard aberto no navegador'), 'desktop/main.js'),
  check('Refresh automático do status', renderer.includes('setInterval'), 'desktop/renderer/app.js'),
  check('Compose final sem agente em Docker', !/^\s+agente:/m.test(compose) && /^\s+api:/m.test(compose) && /^\s+frontend:/m.test(compose) && /^\s+nginx:/m.test(compose), 'docker-compose.desktop.yml'),
  check('Dados persistentes por bind mount', compose.includes('type: bind') && compose.includes('${SOG_DATA_DIR}'), 'docker-compose.desktop.yml'),
  check('Imagens Docker pré-publicáveis', compose.includes('SOG_API_IMAGE') && compose.includes('SOG_FRONTEND_IMAGE') && workflowImages.includes('ghcr.io'), 'docker-compose.desktop.yml + workflow images'),
  check('Agente Python empacotado para Windows', prepare.includes('PyInstaller') && prepare.includes('sog-agent.exe'), 'desktop/scripts/prepare-python-runtime.ps1'),
  check('Playwright + Chromium empacotados', prepare.includes('PLAYWRIGHT_BROWSERS_PATH') && pkg.build.extraResources.some((entry) => entry.to === 'ms-playwright'), 'prepare-python-runtime.ps1 + package.json'),
  check('Smoke do agente empacotado', prepare.includes('--desktop-smoke') && read('agente/src/servico.py').includes('sog-agent-smoke'), 'prepare-python-runtime.ps1 + agente/src/servico.py'),
  check('Controle start/stop do agente local', main.includes('startAgent') && main.includes('stopAgent') && preload.includes('startAgent'), 'desktop/main.js + preload.js'),
  check('Chrome monitorável para login manual', main.includes('openChromeLogin') && html.includes('open-chrome-login') && read('agente/src/modulos/chrome_login_capture.py').includes('connect_over_cdp'), 'desktop + agente/src/modulos/chrome_login_capture.py'),
  check('URLs PJe/SISTJWEB configuráveis com defaults', main.includes('pje.tjdft.jus.br') && main.includes('sistj.tjdft.jus.br'), 'desktop/main.js'),
  check('Credenciais PJe/SISTJWEB não entram no env', main.includes('O SOG não armazenou credenciais de PJe ou SISTJWEB') && docs.includes('nao armazena usuario ou senha'), 'desktop/main.js + docs'),
  check('Storage state em pasta compartilhada', main.includes('STORAGE_STATE_DIR') && main.includes("path.join(dataDir, 'auth')"), 'desktop/main.js'),
  check('Login manual salva storage_state', read('agente/src/modulos/chrome_login_capture.py').includes('storage_state'), 'agente/src/modulos/chrome_login_capture.py'),
  check('Validação PJe preserva downloads', authManager.includes('accept_downloads=accept_downloads') && authManager.includes('new_context('), 'agente/src/modulos/auth_manager.py'),
  check('Mensagens amigáveis de Docker/API/Chrome/login', dashboard.includes('Docker/API offline') && dashboard.includes('Chrome de login indisponível') && dashboard.includes('Sessão PJe pendente') && dashboard.includes('Sessão SISTJWEB pendente'), 'AgenteStatusBar.tsx'),
  check('Diagnóstico exportável sem PII', main.includes('collectDiagnostics') && main.includes('agente-ultimas-linhas.log') && main.includes('redact('), 'desktop/main.js'),
  check('Build Windows automatizado', workflowWindows.includes('windows-latest') && workflowWindows.includes('npm run build:win') && workflowWindows.includes('verify:win-artifact'), '.github/workflows/sog-desktop-windows.yml'),
  check('CI Windows valida smoke de preservação', workflowWindows.includes('smoke:upgrade') && workflowWindows.includes('baseline') && workflowWindows.includes('verify'), '.github/workflows/sog-desktop-windows.yml'),
  check('CI Windows publica resumo de evidência', workflowWindows.includes('GITHUB_STEP_SUMMARY') && workflowWindows.includes('SOG Desktop Windows evidence'), '.github/workflows/sog-desktop-windows.yml'),
  check('Build Windows autocontido valida artefato', pkg.scripts['build:win'].includes('verify:packed-runtime') && pkg.scripts['build:win'].includes('verify:win-artifact'), 'desktop/package.json'),
  check('Smoke Windows operacional', smoke.includes('Assert-Http') && smoke.includes('agent\\sog-agent.exe') && smoke.includes('ms-playwright') && smoke.includes('--desktop-smoke'), 'desktop/scripts/smoke-windows.ps1'),
  check('Smoke de upgrade preserva dados', smokeUpgrade.includes('custas.db') && smokeUpgrade.includes('pje_storage.json') && smokeUpgrade.includes('sistj_storage.json') && smokeUpgrade.includes('upgrade-preservation.pdf') && smokeUpgrade.includes('sentinel.png'), 'desktop/scripts/smoke-upgrade-preservation.ps1'),
  external('Build NSIS executado em Windows 11', 'exige GitHub Actions/Windows real'),
  external('Instalação do .exe em Windows 11', 'exige Windows real'),
  external('Chrome monitorável abrindo PJe/SISTJWEB', 'exige Windows real e acesso operacional aos sistemas'),
]

const ok = results.filter((item) => item.status === 'ok').length
const externalCount = results.filter((item) => item.status === 'external').length

for (const item of results) {
  console.log(`${item.status}\t${item.name}\t${item.evidence}`)
}
console.log(`desktop-plan-audit=ok static=${ok} external=${externalCount}`)
