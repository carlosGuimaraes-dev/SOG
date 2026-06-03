const api = window.sogDesktop
const form = document.querySelector('#config-form')
const logEl = document.querySelector('#log')

function log(message, payload) {
  const time = new Date().toLocaleTimeString('pt-BR')
  const detail = payload ? `\n${JSON.stringify(payload, null, 2)}` : ''
  logEl.textContent = `[${time}] ${message}${detail}\n\n${logEl.textContent}`
}

function setDot(id, status) {
  const el = document.querySelector(id)
  el.className = `dot ${status}`
}

function formData() {
  return Object.fromEntries(new FormData(form).entries())
}

function fillForm(values) {
  for (const [key, value] of Object.entries(values)) {
    if (key === 'secretConfigured') continue
    const input = form.elements.namedItem(key)
    if (input) input.value = value || ''
  }
  if (values.secretConfigured) {
    for (const [key, configured] of Object.entries(values.secretConfigured)) {
      const input = form.elements.namedItem(key)
      if (input && configured) input.placeholder = 'Já configurado; deixe em branco para preservar'
    }
  }
}

async function run(label, fn) {
  try {
    const result = await fn()
    log(result?.message || `${label} concluido.`, result)
    await refresh()
  } catch (error) {
    log(`${label} falhou: ${error.message || error}`)
  }
}

async function refresh() {
  const health = await api.healthcheck()
  const p = await api.paths()
  const configMessage = health.configured
    ? `Dados: ${p.data} · Dashboard: ${health.dashboardUrl || 'http://localhost'}`
    : `Configuração pendente: ${(health.configuration?.missing || []).join(', ')}`
  document.querySelector('#paths').textContent = configMessage

  const dockerOk = health.docker?.running && health.docker?.compose
  setDot('#docker-dot', dockerOk ? 'ok' : health.docker?.installed ? 'warn' : 'bad')
  document.querySelector('#docker-status').textContent = dockerOk ? 'Pronto' : 'Atencao'
  document.querySelector('#docker-message').textContent = health.docker?.message || ''

  const apiOk = health.dashboard?.ok && health.api?.ok
  setDot('#api-dot', apiOk ? 'ok' : 'bad')
  document.querySelector('#api-status').textContent = apiOk ? 'Online' : 'Offline'
  document.querySelector('#api-message').textContent = `Entrada local em ${health.dashboardUrl || 'http://localhost'}`

  setDot('#agent-dot', health.agent?.running ? 'ok' : 'warn')
  document.querySelector('#agent-status').textContent = health.agent?.running
    ? `Rodando (PID ${health.agent.pid})`
    : 'Parado'
}

document.querySelector('#refresh').addEventListener('click', () => run('Atualizar', refresh))
document.querySelector('#open-docker').addEventListener('click', () => run('Abrir Docker Desktop', api.openDockerDesktop))
document.querySelector('#install-docker').addEventListener('click', () => run('Instalar Docker', api.installDockerGuide))
document.querySelector('#choose-data-dir').addEventListener('click', () => run('Escolher pasta', async () => {
  const input = form.elements.namedItem('dataDir')
  const result = await api.chooseDataDir(input?.value || '')
  if (!result.canceled && input) input.value = result.path
  return result
}))
document.querySelector('#save-config').addEventListener('click', () => run('Salvar configuracao', () => api.saveConfig(formData())))
document.querySelector('#start-stack').addEventListener('click', () => run('Subir Docker', api.startStack))
document.querySelector('#restart-stack').addEventListener('click', () => run('Reiniciar Docker', api.restartStack))
document.querySelector('#stop-stack').addEventListener('click', () => run('Parar Docker', api.stopStack))
document.querySelector('#start-agent').addEventListener('click', () => run('Iniciar agente', api.startAgent))
document.querySelector('#open-chrome-login').addEventListener('click', () => run('Abrir Chrome para login', api.openChromeLogin))
document.querySelector('#stop-agent').addEventListener('click', () => run('Parar agente', api.stopAgent))
document.querySelector('#open-dashboard').addEventListener('click', () => run('Abrir dashboard', api.openDashboard))
document.querySelector('#diagnostics').addEventListener('click', () => run('Gerar diagnostico', api.collectDiagnostics))

api.loadConfig()
  .then((config) => {
    fillForm(config)
    return refresh()
  })
  .catch((error) => log(`Inicializacao falhou: ${error.message || error}`))

setInterval(() => {
  refresh().catch((error) => log(`Atualização automática falhou: ${error.message || error}`))
}, 5000)
