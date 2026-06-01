function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function redact(text, extraPaths = []) {
  let output = String(text || '')
    .replace(/(TOKEN|SECRET|SENHA|PASSWORD|API_KEY|CHAT_ID)=.+/gi, '$1=***')
    .replace(/"(TOKEN|SECRET|SENHA|PASSWORD|API_KEY|CHAT_ID|DASHBOARD_SENHA_HASH|JWT_SECRET_KEY)"\s*:\s*"[^"]*"/gi, '"$1": "***"')
    .replace(/(DASHBOARD_SENHA_HASH|JWT_SECRET_KEY)=.+/gi, '$1=***')
    .replace(/\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b/g, '***processo***')
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, '***cpf***')

  for (const candidate of extraPaths.filter(Boolean)) {
    const normalized = String(candidate)
    output = output.replace(new RegExp(escapeRegExp(normalized), 'gi'), '***pasta-local***')
    output = output.replace(new RegExp(escapeRegExp(normalized.replace(/\\/g, '/')), 'gi'), '***pasta-local***')
  }

  return output
}

module.exports = {
  redact,
}
