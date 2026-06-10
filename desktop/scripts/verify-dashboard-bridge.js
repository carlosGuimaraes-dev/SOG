const { DASHBOARD_BRIDGE_PORT, createDashboardBridgeHandler } = require('../lib/dashboard-bridge')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

function createResponseCapture() {
  return {
    statusCode: 200,
    headers: {},
    body: '',
    writeHead(statusCode, headers) {
      this.statusCode = statusCode
      this.headers = headers
    },
    end(chunk = '') {
      this.body += chunk
    },
  }
}

async function invoke(handler, { method = 'POST', url = '/sog/session-browser/open', origin = 'http://localhost' } = {}) {
  const response = createResponseCapture()
  await handler(
    {
      method,
      url,
      headers: origin ? { origin } : {},
    },
    response,
  )
  return {
    ...response,
    json: response.body ? JSON.parse(response.body) : null,
  }
}

async function main() {
  assert(DASHBOARD_BRIDGE_PORT === 47831, 'bridge local deve usar a porta fixa 47831')

  let openChromeLoginCalls = 0
  const handler = createDashboardBridgeHandler({
    openChromeLogin: () => {
      openChromeLoginCalls += 1
      return { ok: true, message: 'Chrome aberto para login em PJe e SISTJWEB.' }
    },
  })

  const success = await invoke(handler)
  assert(success.statusCode === 200, 'POST valido deve responder 200')
  assert(success.headers['Access-Control-Allow-Origin'] === 'http://localhost', 'bridge deve refletir origem local permitida')
  assert(success.json.ok === true, 'bridge deve devolver payload de sucesso')
  assert(openChromeLoginCalls === 1, 'bridge deve acionar openChromeLogin exatamente uma vez')

  const forbidden = await invoke(handler, { origin: 'https://example.com' })
  assert(forbidden.statusCode === 403, 'origem nao local deve ser recusada')

  const failingHandler = createDashboardBridgeHandler({
    openChromeLogin: () => {
      throw new Error('falha simulada')
    },
  })
  const failure = await invoke(failingHandler)
  assert(failure.statusCode === 500, 'falha ao abrir Chrome deve responder 500')
  assert(failure.json.message === 'falha simulada', 'bridge deve propagar a mensagem operacional de erro')

  console.log('dashboard-bridge-verification=ok')
}

main().catch((error) => {
  console.error(error.message)
  process.exit(1)
})