const DASHBOARD_BRIDGE_PORT = 47831
const DASHBOARD_BRIDGE_PATH = '/sog/session-browser/open'

function isAllowedOrigin(origin) {
  if (!origin) return true

  try {
    const parsed = new URL(origin)
    return parsed.protocol === 'http:' && (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1')
  } catch {
    return false
  }
}

function responseHeaders(origin) {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }

  if (origin && isAllowedOrigin(origin)) {
    headers['Access-Control-Allow-Origin'] = origin
  }

  return headers
}

function writeJson(response, statusCode, payload, origin) {
  response.writeHead(statusCode, responseHeaders(origin))
  response.end(JSON.stringify(payload))
}

function createDashboardBridgeHandler({ openChromeLogin }) {
  return async (request, response) => {
    const origin = request.headers.origin

    if (origin && !isAllowedOrigin(origin)) {
      writeJson(response, 403, { ok: false, message: 'Origem não autorizada.' }, origin)
      return
    }

    if (request.method === 'OPTIONS') {
      response.writeHead(204, responseHeaders(origin))
      response.end()
      return
    }

    if (request.url !== DASHBOARD_BRIDGE_PATH) {
      writeJson(response, 404, { ok: false, message: 'Rota não encontrada.' }, origin)
      return
    }

    if (request.method !== 'POST') {
      writeJson(response, 405, { ok: false, message: 'Método não suportado.' }, origin)
      return
    }

    try {
      const result = await Promise.resolve(openChromeLogin())
      writeJson(response, 200, result, origin)
    } catch (error) {
      writeJson(response, 500, {
        ok: false,
        message: error?.message || 'Não foi possível abrir o Navegador de sessão do SOG.',
      }, origin)
    }
  }
}

module.exports = {
  DASHBOARD_BRIDGE_PATH,
  DASHBOARD_BRIDGE_PORT,
  createDashboardBridgeHandler,
}