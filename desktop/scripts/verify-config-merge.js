const {
  chooseSecret,
  missingConfigLabels,
  runtimeConfigMissingLabels,
  secretConfigured,
  validPort,
} = require('../lib/config-merge')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const existing = {
  apiEnv: {
    DASHBOARD_SENHA_HASH: '$2b$12$hash-existente',
    JWT_SECRET_KEY: 'jwt-existente',
  },
  agentEnv: {
    DATAJUD_API_KEY: 'datajud-existente',
    TELEGRAM_BOT_TOKEN: 'telegram-token-existente',
    TELEGRAM_CHAT_ID: 'telegram-chat-existente',
  },
}

const partialInput = {
  dashboardSenha: '',
  pjeUrl: 'https://pje.tjdft.jus.br/pje/login.seam',
  sistjUrl: 'https://sistj.tjdft.jus.br/sistj/sistj',
  datajudApiKey: '',
  telegramBotToken: '',
  telegramChatId: '',
}

assert(missingConfigLabels(partialInput, existing).length === 0, 'config parcial deveria preservar segredos existentes')
assert(chooseSecret('', existing.agentEnv.DATAJUD_API_KEY) === existing.agentEnv.DATAJUD_API_KEY, 'segredo vazio deve preservar existente')
assert(chooseSecret('novo', existing.agentEnv.DATAJUD_API_KEY) === 'novo', 'segredo preenchido deve substituir existente')

const flags = secretConfigured(existing.apiEnv, existing.agentEnv)
assert(flags.dashboardSenha, 'dashboardSenha deveria aparecer como configurado')
assert(flags.datajudApiKey, 'datajudApiKey deveria aparecer como configurado')
assert(flags.telegramBotToken, 'telegramBotToken deveria aparecer como configurado')
assert(flags.telegramChatId, 'telegramChatId deveria aparecer como configurado')
assert(flags.jwtSecret, 'jwtSecret deveria aparecer como configurado')

const missing = missingConfigLabels({
  dashboardSenha: '',
  pjeUrl: '',
  sistjUrl: '',
  datajudApiKey: '',
  telegramBotToken: '',
  telegramChatId: '',
}, { apiEnv: {}, agentEnv: {} })
for (const label of ['URL do PJe', 'URL do SISTJWEB', 'Senha do dashboard', 'Chave Datajud', 'Token do Telegram', 'Chat ID do Telegram']) {
  assert(missing.includes(label), `campo obrigatorio ausente nao reportado: ${label}`)
}

const runtimeMissing = runtimeConfigMissingLabels(
  { DASHBOARD_SENHA_HASH: '$2b$12$hash-existente' },
  {
    PJE_URL: 'https://pje.tjdft.jus.br/pje/login.seam',
    SISTJ_URL: 'https://sistj.tjdft.jus.br/sistj/sistj',
    DATAJUD_API_KEY: 'datajud',
    TELEGRAM_BOT_TOKEN: 'telegram-token',
    TELEGRAM_CHAT_ID: 'telegram-chat',
  },
  {
    SOG_DATA_DIR: 'C:\\Users\\Operador\\AppData\\Local\\SOG\\dados',
    SOG_ENV_API: 'C:\\Users\\Operador\\AppData\\Local\\SOG\\runtime\\.env.api',
    SOG_HTTP_PORT: '8088',
  },
)
assert(runtimeMissing.length === 0, 'runtime completo nao deveria reportar pendencia')

const runtimeBroken = runtimeConfigMissingLabels({}, {}, { SOG_HTTP_PORT: '99999' })
for (const label of ['URL do PJe', 'URL do SISTJWEB', 'Senha do dashboard', 'Pasta de dados', 'Configuração da API para Docker', 'Porta HTTP válida']) {
  assert(runtimeBroken.includes(label), `runtime incompleto nao reportou: ${label}`)
}

assert(validPort('1'), 'porta 1 deveria ser valida')
assert(validPort('65535'), 'porta 65535 deveria ser valida')
assert(!validPort('0'), 'porta 0 deveria ser invalida')
assert(!validPort('99999'), 'porta 99999 deveria ser invalida')
assert(!validPort('abc'), 'porta textual deveria ser invalida')

console.log('config-merge-verification=ok')
