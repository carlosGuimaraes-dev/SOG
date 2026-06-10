const { app, BrowserWindow, dialog, ipcMain, shell } = require('electron')
const { spawn, execFile } = require('node:child_process')
const crypto = require('node:crypto')
const fs = require('node:fs')
const http = require('node:http')
const path = require('node:path')
const {
  chooseSecret,
  hasValue,
  missingConfigLabels,
  runtimeConfigMissingLabels,
  secretConfigured,
  validPort,
} = require('./lib/config-merge')
const { redact } = require('./lib/redact')
const {
  DASHBOARD_BRIDGE_PORT,
  createDashboardBridgeHandler,
} = require('./lib/dashboard-bridge')
const {
  DEFAULT_CHROME_DEBUG_PORT,
  chromeLoginArgs,
  chromeLoginProfileDir,
  findChromeExecutable,
} = require('./lib/chrome-login')

const DOCKER_DESKTOP_URL = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe'
let mainWindow
let agentProcess = null
let agentStartedAt = null
let dashboardBridgeServer = null

function appBaseDir() {
  if (process.platform === 'win32' && process.env.LOCALAPPDATA) {
    return path.join(process.env.LOCALAPPDATA, 'SOG')
  }
  return path.join(app.getPath('userData'), 'SOG')
}

function paths() {
  const base = appBaseDir()
  const savedCompose = readEnvFile(path.join(base, 'runtime', '.env.compose'))
  return {
    base,
    runtime: path.join(base, 'runtime'),
    data: savedCompose.SOG_DATA_DIR || path.join(base, 'dados'),
    auth: path.join(savedCompose.SOG_DATA_DIR || path.join(base, 'dados'), 'auth'),
    logs: path.join(base, 'logs'),
    envApi: path.join(base, 'runtime', '.env.api'),
    envAgent: path.join(base, 'runtime', '.env.agente'),
    envCompose: path.join(base, 'runtime', '.env.compose'),
  }
}

function runtimeRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'sog-runtime')
  }
  return path.resolve(__dirname, '..')
}

function ensureDirs() {
  const p = paths()
  for (const dir of [p.base, p.runtime, p.data, p.auth, p.logs]) {
    fs.mkdirSync(dir, { recursive: true })
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 980,
    minHeight: 680,
    title: 'SOG Desktop',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'))
}

function execPromise(command, args, options = {}) {
  return new Promise((resolve) => {
    execFile(command, args, { timeout: 30000, ...options }, (error, stdout, stderr) => {
      resolve({
        ok: !error,
        code: error?.code ?? 0,
        stdout: String(stdout || '').trim(),
        stderr: String(stderr || '').trim(),
        error: error?.message || '',
      })
    })
  })
}

async function dockerComposeArgs() {
  const composeV2 = await execPromise('docker', ['compose', 'version'])
  if (composeV2.ok) {
    return { command: 'docker', prefix: ['compose'] }
  }
  const composeV1 = await execPromise('docker-compose', ['version'])
  if (composeV1.ok) {
    return { command: 'docker-compose', prefix: [] }
  }
  return null
}

function composeEnv() {
  const p = paths()
  const savedCompose = readEnvFile(p.envCompose)
  return {
    ...process.env,
    SOG_DATA_DIR: toDockerPath(savedCompose.SOG_DATA_DIR || p.data),
    SOG_ENV_API: toDockerPath(savedCompose.SOG_ENV_API || p.envApi),
    SOG_API_IMAGE: savedCompose.SOG_API_IMAGE || process.env.SOG_API_IMAGE || 'sog-api:local',
    SOG_FRONTEND_IMAGE: savedCompose.SOG_FRONTEND_IMAGE || process.env.SOG_FRONTEND_IMAGE || 'sog-frontend:local',
    SOG_IMAGE_PULL_POLICY: savedCompose.SOG_IMAGE_PULL_POLICY || process.env.SOG_IMAGE_PULL_POLICY || 'missing',
    SOG_HTTP_PORT: savedCompose.SOG_HTTP_PORT || process.env.SOG_HTTP_PORT || '80',
  }
}

function toDockerPath(filePath) {
  return process.platform === 'win32' ? String(filePath).replace(/\\/g, '/') : filePath
}

function httpPort() {
  const savedCompose = readEnvFile(paths().envCompose)
  return savedCompose.SOG_HTTP_PORT || process.env.SOG_HTTP_PORT || '80'
}

function dashboardUrl() {
  const port = httpPort()
  return dashboardUrlForPort(port)
}

function dashboardUrlForPort(port) {
  return port === '80' ? 'http://localhost' : `http://localhost:${port}`
}

async function checkDocker() {
  const client = await execPromise('docker', ['version', '--format', '{{.Client.Version}}'])
  if (!client.ok) {
    return {
      installed: false,
      running: false,
      message: 'Docker Desktop não foi encontrado. Instale o Docker Desktop e volte ao SOG.',
    }
  }
  const server = await execPromise('docker', ['version', '--format', '{{.Server.Version}}'])
  if (!server.ok) {
    return {
      installed: true,
      running: false,
      clientVersion: client.stdout,
      message: 'Docker Desktop está instalado, mas o serviço não está em execução.',
    }
  }
  const compose = await dockerComposeArgs()
  return {
    installed: true,
    running: true,
    compose: Boolean(compose),
    clientVersion: client.stdout,
    serverVersion: server.stdout,
    message: compose
      ? 'Docker Desktop pronto.'
      : 'Docker está ativo, mas o Docker Compose não respondeu.',
  }
}

async function installDockerGuide() {
  await shell.openExternal(DOCKER_DESKTOP_URL)
  return {
    message: 'Abrimos o instalador oficial do Docker Desktop. Conclua a instalação e volte ao SOG Desktop.',
  }
}

async function openDockerDesktop() {
  if (process.platform === 'win32') {
    const candidates = [
      path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Docker', 'Docker', 'Docker Desktop.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Docker', 'Docker Desktop.exe'),
    ]
    const dockerExe = candidates.find((candidate) => candidate && fs.existsSync(candidate))
    if (dockerExe) {
      spawn(dockerExe, [], { detached: true, stdio: 'ignore' }).unref()
      return {
        ok: true,
        message: 'Abrimos o Docker Desktop. Aguarde ele ficar pronto e clique em Atualizar.',
      }
    }
  }

  await shell.openExternal('docker-desktop://dashboard')
  return {
    ok: true,
    message: 'Tentamos abrir o Docker Desktop. Aguarde ele ficar pronto e clique em Atualizar.',
  }
}

async function chooseDataDir(currentPath) {
  ensureDirs()
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Escolha a pasta de dados do SOG',
    defaultPath: currentPath || paths().data,
    properties: ['openDirectory', 'createDirectory'],
  })
  if (result.canceled || !result.filePaths.length) {
    return { canceled: true }
  }
  return {
    canceled: false,
    path: result.filePaths[0],
    message: 'Pasta de dados selecionada.',
  }
}

function writeEnvFile(filePath, values) {
  const lines = Object.entries(values).map(([key, value]) => `${key}=${formatEnvValue(value)}`)
  fs.writeFileSync(filePath, `${lines.join('\n')}\n`, { mode: 0o600 })
}

function formatEnvValue(value) {
  const normalized = String(value ?? '').replace(/\r?\n/g, ' ')
  if (!/[#\s"'\\]/.test(normalized)) return normalized
  return `"${normalized.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function parseEnvValue(value) {
  const trimmed = value.trim()
  if (trimmed.length >= 2 && trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed
      .slice(1, -1)
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\')
  }
  return value
}

function readEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}
  const env = {}
  for (const rawLine of fs.readFileSync(filePath, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eq = line.indexOf('=')
    if (eq === -1) continue
    env[line.slice(0, eq)] = parseEnvValue(line.slice(eq + 1))
  }
  return env
}

function defaultConfig() {
  const p = paths()
  return {
    pjeUrl: 'https://pje.tjdft.jus.br/pje/login.seam',
    pjeEtiqueta: 'SHEILA DE DEUS (TREINAMENTO)',
    sistjUrl: 'https://sistj.tjdft.jus.br/sistj/sistj',
    datajudUrl: 'https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search',
    datajudApiKey: '',
    telegramBotToken: '',
    telegramChatId: '',
    dataDir: p.data,
    httpPort: process.env.SOG_HTTP_PORT || '80',
    apiImage: process.env.SOG_API_IMAGE || 'sog-api:local',
    frontendImage: process.env.SOG_FRONTEND_IMAGE || 'sog-frontend:local',
    imagePullPolicy: process.env.SOG_IMAGE_PULL_POLICY || 'missing',
  }
}

function existingConfig() {
  const p = paths()
  const apiEnv = readEnvFile(p.envApi)
  const agentEnv = readEnvFile(p.envAgent)
  const composeEnv = readEnvFile(p.envCompose)
  return { apiEnv, agentEnv, composeEnv }
}

function loadConfig() {
  const defaults = defaultConfig()
  const { apiEnv, agentEnv, composeEnv } = existingConfig()
  return {
    ...defaults,
    pjeUrl: agentEnv.PJE_URL || defaults.pjeUrl,
    pjeEtiqueta: agentEnv.PJE_ETIQUETA || defaults.pjeEtiqueta,
    sistjUrl: agentEnv.SISTJ_URL || defaults.sistjUrl,
    datajudUrl: agentEnv.DATAJUD_URL || defaults.datajudUrl,
    datajudApiKey: '',
    telegramBotToken: '',
    telegramChatId: '',
    dataDir: composeEnv.SOG_DATA_DIR || defaults.dataDir,
    httpPort: composeEnv.SOG_HTTP_PORT || defaults.httpPort,
    apiImage: composeEnv.SOG_API_IMAGE || defaults.apiImage,
    frontendImage: composeEnv.SOG_FRONTEND_IMAGE || defaults.frontendImage,
    imagePullPolicy: composeEnv.SOG_IMAGE_PULL_POLICY || defaults.imagePullPolicy,
    secretConfigured: secretConfigured(apiEnv, agentEnv),
  }
}

function configurationStatus() {
  const p = paths()
  const { apiEnv, agentEnv, composeEnv } = existingConfig()
  const requiredFiles = [
    [p.envApi, 'Configuração da API'],
    [p.envAgent, 'Configuração do agente'],
    [p.envCompose, 'Configuração do Docker'],
  ]
  const missing = requiredFiles
    .filter(([filePath]) => !fs.existsSync(filePath))
    .map(([, label]) => label)
  if (missing.length === 0) {
    missing.push(...runtimeConfigMissingLabels(apiEnv, agentEnv, composeEnv))
  }
  return {
    ok: missing.length === 0,
    missing,
    filesOk: requiredFiles.every(([filePath]) => fs.existsSync(filePath)),
    paths: p,
  }
}

function validateConfig(input, existing = existingConfig()) {
  const missing = missingConfigLabels(input, existing)
  if (missing.length) {
    throw new Error(`Preencha os campos obrigatórios: ${missing.join(', ')}.`)
  }
}

async function saveConfig(input) {
  ensureDirs()
  const p = paths()
  const config = { ...defaultConfig(), ...input }
  const existing = existingConfig()
  validateConfig(config, existing)
  if (!validPort(config.httpPort || '80')) {
    throw new Error('A porta HTTP do dashboard deve ser um número entre 1 e 65535.')
  }
  const dataDir = config.dataDir || p.data
  fs.mkdirSync(dataDir, { recursive: true })
  fs.mkdirSync(path.join(dataDir, 'auth'), { recursive: true })
  const jwtSecret = existing.apiEnv.JWT_SECRET_KEY || crypto.randomBytes(32).toString('hex')
  writeEnvFile(p.envApi, {
    DASHBOARD_AUTH_DISABLED: 'true',
    DASHBOARD_LOCAL_USER: 'operador-local',
    JWT_SECRET_KEY: jwtSecret,
    FRONTEND_URL: dashboardUrlForPort(config.httpPort || existing.composeEnv.SOG_HTTP_PORT || '80'),
    DB_PATH: '/dados/custas.db',
  })
  writeEnvFile(p.envAgent, {
    PJE_URL: config.pjeUrl,
    PJE_ETIQUETA: config.pjeEtiqueta,
    SISTJ_URL: config.sistjUrl,
    DATAJUD_API_KEY: chooseSecret(config.datajudApiKey, existing.agentEnv.DATAJUD_API_KEY),
    DATAJUD_URL: config.datajudUrl,
    TELEGRAM_BOT_TOKEN: chooseSecret(config.telegramBotToken, existing.agentEnv.TELEGRAM_BOT_TOKEN),
    TELEGRAM_CHAT_ID: chooseSecret(config.telegramChatId, existing.agentEnv.TELEGRAM_CHAT_ID),
    DB_PATH: path.join(dataDir, 'custas.db'),
    STORAGE_STATE_DIR: path.join(dataDir, 'auth'),
    HEADLESS: 'false',
    MAX_TENTATIVAS: '3',
    TIMEOUT_PADRAO: '30000',
  })
  writeEnvFile(p.envCompose, {
    SOG_DATA_DIR: toDockerPath(dataDir),
    SOG_ENV_API: toDockerPath(p.envApi),
    SOG_HTTP_PORT: config.httpPort || existing.composeEnv.SOG_HTTP_PORT || '80',
    SOG_API_IMAGE: config.apiImage || existing.composeEnv.SOG_API_IMAGE || 'sog-api:local',
    SOG_FRONTEND_IMAGE: config.frontendImage || existing.composeEnv.SOG_FRONTEND_IMAGE || 'sog-frontend:local',
    SOG_IMAGE_PULL_POLICY: config.imagePullPolicy || existing.composeEnv.SOG_IMAGE_PULL_POLICY || 'missing',
  })
  return {
    ok: true,
    message: 'Configuração salva. O SOG não armazenou credenciais de PJe ou SISTJWEB.',
    paths: p,
  }
}

async function startStack() {
  ensureDirs()
  const docker = await checkDocker()
  if (!docker.running) throw new Error(docker.message)
  const compose = await dockerComposeArgs()
  if (!compose) throw new Error('Docker Compose não respondeu dentro do Docker Desktop.')
  const composeFile = path.join(runtimeRoot(), 'docker-compose.desktop.yml')
  const config = configurationStatus()
  if (!config.ok) {
    throw new Error(`Configure o SOG Desktop antes de subir a stack: ${config.missing.join(', ')}.`)
  }
  const args = [
    ...compose.prefix,
    '-f',
    composeFile,
    '--env-file',
    paths().envCompose,
    '-p',
    'sog-desktop',
    'up',
    '-d',
  ]
  const env = composeEnv()
  if (env.SOG_API_IMAGE.endsWith(':local') || env.SOG_FRONTEND_IMAGE.endsWith(':local')) {
    args.push('--build')
  }
  const result = await execPromise(compose.command, args, { cwd: runtimeRoot(), env, timeout: 20 * 60 * 1000 })
  if (!result.ok) throw new Error(result.stderr || result.error || 'Falha ao subir Docker.')
  await shell.openExternal(dashboardUrl())
  return { ok: true, message: 'Stack Docker iniciada. Dashboard aberto no navegador.', output: result.stdout }
}

function composeUpArgs(forceRecreate = false) {
  const args = [
    '-f',
    path.join(runtimeRoot(), 'docker-compose.desktop.yml'),
    '--env-file',
    paths().envCompose,
    '-p',
    'sog-desktop',
    'up',
    '-d',
  ]
  if (forceRecreate) {
    args.push('--force-recreate')
  }
  const env = composeEnv()
  if (env.SOG_API_IMAGE.endsWith(':local') || env.SOG_FRONTEND_IMAGE.endsWith(':local')) {
    args.push('--build')
  }
  return args
}

async function restartStack() {
  ensureDirs()
  const docker = await checkDocker()
  if (!docker.running) throw new Error(docker.message)
  const compose = await dockerComposeArgs()
  if (!compose) throw new Error('Docker Compose não respondeu dentro do Docker Desktop.')
  const config = configurationStatus()
  if (!config.ok) {
    throw new Error(`Configure o SOG Desktop antes de reiniciar a stack: ${config.missing.join(', ')}.`)
  }
  const result = await execPromise(compose.command, [...compose.prefix, ...composeUpArgs(true)], {
    cwd: runtimeRoot(),
    env: composeEnv(),
    timeout: 20 * 60 * 1000,
  })
  if (!result.ok) throw new Error(result.stderr || result.error || 'Falha ao reiniciar Docker.')
  await shell.openExternal(dashboardUrl())
  return { ok: true, message: 'Stack Docker reiniciada. Dashboard aberto no navegador.', output: result.stdout }
}

async function stopStack() {
  const config = configurationStatus()
  if (!config.ok) {
    return { ok: true, message: 'Stack Docker já está parada; configuração local ainda não foi criada.' }
  }
  const compose = await dockerComposeArgs()
  if (!compose) throw new Error('Docker Compose não respondeu dentro do Docker Desktop.')
  const args = [
    ...compose.prefix,
    '-f',
    path.join(runtimeRoot(), 'docker-compose.desktop.yml'),
    '--env-file',
    paths().envCompose,
    '-p',
    'sog-desktop',
    'down',
  ]
  const result = await execPromise(compose.command, args, { cwd: runtimeRoot(), env: composeEnv(), timeout: 120000 })
  if (!result.ok) throw new Error(result.stderr || result.error || 'Falha ao parar Docker.')
  return { ok: true, message: 'Stack Docker parada.' }
}

function httpGet(url) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: 5000 }, (res) => {
      res.resume()
      resolve({ ok: res.statusCode >= 200 && res.statusCode < 500, status: res.statusCode })
    })
    req.on('timeout', () => {
      req.destroy()
      resolve({ ok: false, status: 0 })
    })
    req.on('error', () => resolve({ ok: false, status: 0 }))
  })
}

async function healthcheck() {
  const docker = await checkDocker()
  const url = dashboardUrl()
  const dashboard = await httpGet(url)
  const api = await httpGet(`${url}/api/v1/health`)
  const config = configurationStatus()
  return {
    docker,
    dashboard,
    api,
    agent: agentStatus(),
    configured: config.ok,
    configuration: config,
    dashboardUrl: url,
    paths: paths(),
  }
}

function findBundledAgent() {
  const exe = process.platform === 'win32' ? 'sog-agent.exe' : 'sog-agent'
  const candidates = [
    path.join(process.resourcesPath || '', 'agent', exe),
    path.join(__dirname, 'vendor', 'agent', exe),
  ]
  return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || null
}

function findPython() {
  if (process.env.SOG_PYTHON) return process.env.SOG_PYTHON
  if (app.isPackaged) {
    const exe = process.platform === 'win32' ? 'python.exe' : 'python'
    const candidates = [
      path.join(process.resourcesPath, 'python', exe),
      path.join(process.resourcesPath, 'python', 'Scripts', exe),
      path.join(process.resourcesPath, 'python', 'bin', exe),
    ]
    for (const bundled of candidates) {
      if (fs.existsSync(bundled)) return bundled
    }
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

function playwrightBrowsersPath() {
  const candidates = [
    path.join(process.resourcesPath || '', 'ms-playwright'),
    path.join(__dirname, 'vendor', 'ms-playwright'),
  ]
  return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || null
}

function agentCommand(args = []) {
  const root = runtimeRoot()
  const script = path.join(root, 'agente', 'src', 'servico.py')
  const bundledAgent = findBundledAgent()
  return {
    root,
    command: bundledAgent || findPython(),
    args: bundledAgent ? args : [script, ...args],
    bundledAgent,
  }
}

function agentEnv() {
  const root = runtimeRoot()
  const envAgent = readEnvFile(paths().envAgent)
  const browsersPath = playwrightBrowsersPath()
  const pythonPath = [path.join(root, 'shared'), path.join(root, 'agente', 'src'), process.env.PYTHONPATH || '']
    .filter(Boolean)
    .join(path.delimiter)
  return {
    ...process.env,
    ...envAgent,
    PYTHONPATH: pythonPath,
    ...(browsersPath ? { PLAYWRIGHT_BROWSERS_PATH: browsersPath } : {}),
    HEADLESS: 'false',
  }
}

function startAgent() {
  ensureDirs()
  if (agentProcess && !agentProcess.killed) {
    return { ok: true, message: 'Agente desktop já está em execução.', status: agentStatus() }
  }
  const config = configurationStatus()
  if (!config.ok) {
    throw new Error(`Configure o SOG Desktop antes de iniciar o agente: ${config.missing.join(', ')}.`)
  }
  const logPath = path.join(paths().logs, `agente-${new Date().toISOString().slice(0, 10)}.log`)
  const logStream = fs.createWriteStream(logPath, { flags: 'a' })
  const agent = agentCommand()

  agentProcess = spawn(agent.command, agent.args, {
    cwd: agent.root,
    env: agentEnv(),
    windowsHide: false,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  agentStartedAt = new Date().toISOString()
  agentProcess.stdout.pipe(logStream)
  agentProcess.stderr.pipe(logStream)
  agentProcess.on('error', (error) => {
    logStream.write(`\n[desktop] falha ao iniciar agente: ${error.message}\n`)
    logStream.end()
    agentProcess = null
  })
  agentProcess.on('exit', (code, signal) => {
    logStream.write(`\n[desktop] agente finalizado code=${code} signal=${signal}\n`)
    logStream.end()
    agentProcess = null
  })
  return { ok: true, message: 'Agente desktop iniciado.', status: agentStatus() }
}

function openChromeLogin() {
  ensureDirs()
  const config = configurationStatus()
  if (!config.ok) {
    throw new Error(`Configure o SOG Desktop antes de abrir o Chrome para login: ${config.missing.join(', ')}.`)
  }
  const chromePath = findChromeExecutable()
  if (!chromePath) {
    throw new Error('Google Chrome não encontrado. Instale o Google Chrome para realizar o login monitorável.')
  }
  const cfg = loadConfig()
  const profileDir = chromeLoginProfileDir(paths().data)
  fs.mkdirSync(profileDir, { recursive: true })
  const child = spawn(chromePath, chromeLoginArgs({
    profileDir,
    pjeUrl: cfg.pjeUrl,
    sistjUrl: cfg.sistjUrl,
    remoteDebuggingPort: DEFAULT_CHROME_DEBUG_PORT,
  }), {
    detached: true,
    stdio: 'ignore',
    windowsHide: false,
  })
  child.unref()
  return {
    ok: true,
    message: 'Chrome aberto para login em PJe e SISTJWEB.',
    remoteDebuggingPort: DEFAULT_CHROME_DEBUG_PORT,
    profileDir,
  }
}

function stopAgent() {
  if (!agentProcess) {
    return { ok: true, message: 'Agente desktop já estava parado.', status: agentStatus() }
  }
  agentProcess.kill('SIGTERM')
  return { ok: true, message: 'Parada do agente desktop solicitada.', status: agentStatus() }
}

function agentStatus() {
  return {
    running: Boolean(agentProcess && !agentProcess.killed),
    pid: agentProcess?.pid || null,
    startedAt: agentStartedAt,
  }
}

function tailFile(filePath, maxBytes = 20000) {
  if (!filePath || !fs.existsSync(filePath)) return null
  const stat = fs.statSync(filePath)
  const size = Math.min(stat.size, maxBytes)
  const fd = fs.openSync(filePath, 'r')
  try {
    const buffer = Buffer.alloc(size)
    fs.readSync(fd, buffer, 0, size, Math.max(0, stat.size - size))
    return buffer.toString('utf8')
  } finally {
    fs.closeSync(fd)
  }
}

function latestAgentLog() {
  const p = paths()
  if (!fs.existsSync(p.logs)) return null
  const files = fs.readdirSync(p.logs)
    .filter((file) => file.startsWith('agente-') && file.endsWith('.log'))
    .map((file) => path.join(p.logs, file))
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)
  return files[0] || null
}

async function composeSnapshot() {
  const config = configurationStatus()
  if (!config.ok) {
    return { ok: false, skipped: true, reason: 'Configuração local incompleta.' }
  }
  const compose = await dockerComposeArgs()
  if (!compose) {
    return { ok: false, skipped: true, reason: 'Docker Compose indisponível.' }
  }
  const commonArgs = [
    ...compose.prefix,
    '-f',
    path.join(runtimeRoot(), 'docker-compose.desktop.yml'),
    '--env-file',
    paths().envCompose,
    '-p',
    'sog-desktop',
  ]
  return {
    services: await execPromise(compose.command, [...commonArgs, 'config', '--services'], {
      cwd: runtimeRoot(),
      env: composeEnv(),
    }),
    ps: await execPromise(compose.command, [...commonArgs, 'ps'], {
      cwd: runtimeRoot(),
      env: composeEnv(),
    }),
  }
}

async function collectDiagnostics() {
  ensureDirs()
  const logPath = latestAgentLog()
  const redactionPaths = [
    process.env.USERPROFILE,
    process.env.HOME,
    process.env.LOCALAPPDATA,
    process.env.APPDATA,
    app.getPath('home'),
    app.getPath('userData'),
    paths().base,
  ]
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  const packageDir = path.join(paths().logs, `diagnostico-${stamp}`)
  fs.mkdirSync(packageDir, { recursive: true })
  const agentLogTail = logPath ? tailFile(logPath) : null
  const snapshot = {
    createdAt: new Date().toISOString(),
    app: {
      version: app.getVersion(),
      packaged: app.isPackaged,
      platform: process.platform,
      arch: process.arch,
    },
    runtimeRoot: runtimeRoot(),
    resources: {
      bundledAgent: findBundledAgent(),
      playwrightBrowsers: playwrightBrowsersPath(),
    },
    configuration: configurationStatus(),
    health: await healthcheck(),
    dockerVersion: await execPromise('docker', ['version']),
    docker: await execPromise('docker', ['ps', '--format', '{{.Names}} {{.Status}}']),
    compose: await composeSnapshot(),
    latestAgentLog: logPath ? {
      path: logPath,
      tail: agentLogTail,
    } : null,
  }
  const filePath = path.join(packageDir, 'diagnostico.json')
  fs.writeFileSync(filePath, redact(JSON.stringify(snapshot, null, 2), redactionPaths))
  if (agentLogTail) {
    fs.writeFileSync(path.join(packageDir, 'agente-ultimas-linhas.log'), redact(agentLogTail, redactionPaths))
  }
  await shell.openPath(packageDir)
  return {
    ok: true,
    path: packageDir,
    file: filePath,
    message: 'Pacote de diagnóstico gerado e pasta aberta.',
  }
}

function openDashboard() {
  shell.openExternal(dashboardUrl())
  return { ok: true, message: 'Dashboard aberto no navegador.' }
}

function startDashboardBridge() {
  if (dashboardBridgeServer) return dashboardBridgeServer

  dashboardBridgeServer = http.createServer(createDashboardBridgeHandler({
    openChromeLogin,
  }))
  dashboardBridgeServer.on('error', (error) => {
    console.error(`[dashboard-bridge] ${error.message}`)
  })
  dashboardBridgeServer.listen(DASHBOARD_BRIDGE_PORT, '127.0.0.1')
  return dashboardBridgeServer
}

function stopDashboardBridge() {
  if (!dashboardBridgeServer) return
  dashboardBridgeServer.close()
  dashboardBridgeServer = null
}

function wireIpc() {
  ipcMain.handle('sog:paths', () => paths())
  ipcMain.handle('sog:configuration-status', () => configurationStatus())
  ipcMain.handle('sog:default-config', () => defaultConfig())
  ipcMain.handle('sog:load-config', () => loadConfig())
  ipcMain.handle('sog:check-docker', () => checkDocker())
  ipcMain.handle('sog:install-docker-guide', () => installDockerGuide())
  ipcMain.handle('sog:open-docker-desktop', () => openDockerDesktop())
  ipcMain.handle('sog:choose-data-dir', (_event, currentPath) => chooseDataDir(currentPath))
  ipcMain.handle('sog:save-config', (_event, input) => saveConfig(input))
  ipcMain.handle('sog:start-stack', () => startStack())
  ipcMain.handle('sog:restart-stack', () => restartStack())
  ipcMain.handle('sog:stop-stack', () => stopStack())
  ipcMain.handle('sog:healthcheck', () => healthcheck())
  ipcMain.handle('sog:start-agent', () => startAgent())
  ipcMain.handle('sog:open-chrome-login', () => openChromeLogin())
  ipcMain.handle('sog:stop-agent', () => stopAgent())
  ipcMain.handle('sog:agent-status', () => agentStatus())
  ipcMain.handle('sog:collect-diagnostics', () => collectDiagnostics())
  ipcMain.handle('sog:open-dashboard', () => openDashboard())
}

app.whenReady().then(() => {
  ensureDirs()
  startDashboardBridge()
  wireIpc()
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  stopDashboardBridge()
  if (agentProcess) agentProcess.kill('SIGTERM')
})
