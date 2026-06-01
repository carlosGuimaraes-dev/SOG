const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
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

const values = {
  SOG_DATA_DIR: 'C:\\Users\\Carlos Guimaraes\\AppData\\Local\\SOG\\dados',
  SOG_ENV_API: 'C:\\Users\\Carlos Guimaraes\\AppData\\Local\\SOG\\runtime\\.env.api',
  TOKEN: 'abc#123',
}

const envText = Object.entries(values)
  .map(([key, value]) => `${key}=${formatEnvValue(value)}`)
  .join('\n')

const parsed = Object.fromEntries(
  envText.split('\n').map((line) => {
    const index = line.indexOf('=')
    return [line.slice(0, index), parseEnvValue(line.slice(index + 1))]
  }),
)

for (const [key, value] of Object.entries(values)) {
  assert(parsed[key] === value, `${key} nao preservou valor com espacos/barras`)
}

const tmp = path.join(os.tmpdir(), `sog-env-format-${Date.now()}.env`)
fs.writeFileSync(tmp, `${envText}\n`)
assert(fs.readFileSync(tmp, 'utf8').includes('"C:\\\\Users\\\\Carlos Guimaraes'), 'path Windows deve ser escrito entre aspas')
fs.unlinkSync(tmp)

console.log('env-format-verification=ok')
