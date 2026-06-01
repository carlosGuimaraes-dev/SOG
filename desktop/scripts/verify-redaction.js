const { redact } = require('../lib/redact')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const input = [
  'DATAJUD_API_KEY=abc123',
  '"JWT_SECRET_KEY": "super-secreto"',
  'processo 0732384-63.2024.8.07.0001',
  'cpf 123.456.789-10',
  'C:\\Users\\Carlos Guimaraes\\AppData\\Local\\SOG\\dados',
].join('\n')

const output = redact(input, ['C:\\Users\\Carlos Guimaraes'])

for (const forbidden of ['abc123', 'super-secreto', '0732384-63.2024.8.07.0001', '123.456.789-10', 'Carlos Guimaraes']) {
  assert(!output.includes(forbidden), `redacao deixou vazar: ${forbidden}`)
}

for (const expected of ['DATAJUD_API_KEY=***', '"JWT_SECRET_KEY": "***"', '***processo***', '***cpf***', '***pasta-local***']) {
  assert(output.includes(expected), `redacao esperada ausente: ${expected}`)
}

console.log('redaction-verification=ok')
