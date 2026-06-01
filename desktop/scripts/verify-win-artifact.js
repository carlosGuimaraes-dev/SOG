const fs = require('node:fs')
const path = require('node:path')

const desktopRoot = path.resolve(__dirname, '..')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

function exists(relativePath) {
  return fs.existsSync(path.join(desktopRoot, relativePath))
}

const distDir = path.join(desktopRoot, 'dist')
assert(fs.existsSync(distDir), 'desktop/dist nao existe')

const installers = fs.readdirSync(distDir)
  .filter((file) => file.toLowerCase().endsWith('.exe'))
  .filter((file) => !file.toLowerCase().includes('uninstaller'))

assert(installers.length > 0, 'instalador Windows .exe nao encontrado em desktop/dist')
assert(exists('vendor/agent/sog-agent.exe'), 'vendor/agent/sog-agent.exe nao foi gerado')
assert(exists('vendor/ms-playwright'), 'vendor/ms-playwright nao foi gerado')

const browserEntries = fs.readdirSync(path.join(desktopRoot, 'vendor', 'ms-playwright'))
  .filter((entry) => !entry.startsWith('.'))
assert(browserEntries.length > 0, 'vendor/ms-playwright esta vazio')

const resourcesDir = path.join(distDir, 'win-unpacked', 'resources')
assert(fs.existsSync(resourcesDir), 'resources do win-unpacked nao encontrado')
for (const relativePath of [
  'sog-runtime/docker-compose.desktop.yml',
  'sog-runtime/api/Dockerfile',
  'sog-runtime/api/src/app.py',
  'sog-runtime/frontend/Dockerfile',
  'sog-runtime/shared/sog_shared/schema.sql',
  'sog-runtime/nginx/nginx.conf',
]) {
  assert(fs.existsSync(path.join(resourcesDir, relativePath)), `runtime Windows incompleto: ${relativePath}`)
}

console.log(`windows-installer=${installers[0]}`)
console.log('windows-artifact-verification=ok')
