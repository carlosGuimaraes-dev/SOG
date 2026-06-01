function hasValue(value) {
  return String(value || '').trim().length > 0
}

function chooseSecret(inputValue, existingValue) {
  return hasValue(inputValue) ? inputValue : existingValue
}

function missingConfigLabels(input, existing) {
  const required = [
    ['pjeUrl', 'URL do PJe'],
    ['sistjUrl', 'URL do SISTJWEB'],
  ]
  const secretRequired = [
    ['dashboardSenha', existing.apiEnv?.DASHBOARD_SENHA_HASH, 'Senha do dashboard'],
    ['datajudApiKey', existing.agentEnv?.DATAJUD_API_KEY, 'Chave Datajud'],
    ['telegramBotToken', existing.agentEnv?.TELEGRAM_BOT_TOKEN, 'Token do Telegram'],
    ['telegramChatId', existing.agentEnv?.TELEGRAM_CHAT_ID, 'Chat ID do Telegram'],
  ]
  const missing = required
    .filter(([key]) => !hasValue(input[key]))
    .map(([, label]) => label)
  for (const [key, currentValue, label] of secretRequired) {
    if (!hasValue(input[key]) && !hasValue(currentValue)) {
      missing.push(label)
    }
  }
  return missing
}

function secretConfigured(apiEnv, agentEnv) {
  return {
    dashboardSenha: hasValue(apiEnv.DASHBOARD_SENHA_HASH),
    datajudApiKey: hasValue(agentEnv.DATAJUD_API_KEY),
    telegramBotToken: hasValue(agentEnv.TELEGRAM_BOT_TOKEN),
    telegramChatId: hasValue(agentEnv.TELEGRAM_CHAT_ID),
    jwtSecret: hasValue(apiEnv.JWT_SECRET_KEY),
  }
}

function validPort(value) {
  if (!/^\d+$/.test(String(value || ''))) return false
  const port = Number(value)
  return port >= 1 && port <= 65535
}

function runtimeConfigMissingLabels(apiEnv, agentEnv, composeEnv) {
  const missing = missingConfigLabels({
    dashboardSenha: apiEnv.DASHBOARD_SENHA_HASH ? 'configurado' : '',
    pjeUrl: agentEnv.PJE_URL,
    sistjUrl: agentEnv.SISTJ_URL,
    datajudApiKey: agentEnv.DATAJUD_API_KEY,
    telegramBotToken: agentEnv.TELEGRAM_BOT_TOKEN,
    telegramChatId: agentEnv.TELEGRAM_CHAT_ID,
  }, { apiEnv: {}, agentEnv: {} })

  if (!hasValue(composeEnv.SOG_DATA_DIR)) missing.push('Pasta de dados')
  if (!hasValue(composeEnv.SOG_ENV_API)) missing.push('Configuração da API para Docker')
  if (!hasValue(composeEnv.SOG_HTTP_PORT)) missing.push('Porta HTTP do dashboard')
  if (hasValue(composeEnv.SOG_HTTP_PORT) && !validPort(composeEnv.SOG_HTTP_PORT)) {
    missing.push('Porta HTTP válida')
  }

  return [...new Set(missing)]
}

module.exports = {
  chooseSecret,
  hasValue,
  missingConfigLabels,
  runtimeConfigMissingLabels,
  secretConfigured,
  validPort,
}
