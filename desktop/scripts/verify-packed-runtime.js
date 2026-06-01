const fs = require('node:fs')
const path = require('node:path')

const desktopRoot = path.resolve(__dirname, '..')
const distRoot = path.join(desktopRoot, 'dist')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

function findResourcesDir() {
  const candidates = [
    path.join(distRoot, 'win-unpacked', 'resources'),
    path.join(distRoot, 'mac', 'SOG Desktop.app', 'Contents', 'Resources'),
    path.join(distRoot, 'linux-unpacked', 'resources'),
  ]
  return candidates.find((candidate) => fs.existsSync(candidate))
}

const resourcesDir = findResourcesDir()
assert(resourcesDir, 'diretorio resources do app empacotado nao encontrado')

const required = [
  ['app.asar', 'app Electron empacotado'],
  ['sog-runtime/docker-compose.desktop.yml', 'Compose desktop'],
  ['sog-runtime/api/Dockerfile', 'Dockerfile da API'],
  ['sog-runtime/api/src/app.py', 'app FastAPI'],
  ['sog-runtime/api/src/rotas/agente.py', 'rotas do agente na API'],
  ['sog-runtime/frontend/Dockerfile', 'Dockerfile do frontend'],
  ['sog-runtime/frontend/src/components/agente/AgenteStatusBar.tsx', 'dashboard do agente'],
  ['sog-runtime/shared/sog_shared/schema.sql', 'schema SQLite compartilhado'],
  ['sog-runtime/nginx/nginx.conf', 'config nginx'],
]

for (const [relativePath, label] of required) {
  assert(fs.existsSync(path.join(resourcesDir, relativePath)), `${label} ausente no runtime empacotado: ${relativePath}`)
}

console.log(`packed-runtime=${resourcesDir}`)
console.log('packed-runtime-verification=ok')
