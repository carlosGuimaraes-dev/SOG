const path = require('node:path')
const {
  chromeLoginArgs,
  chromeLoginProfileDir,
  findChromeExecutable,
} = require('../lib/chrome-login')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const profileDir = chromeLoginProfileDir(path.join('C:', 'SOG', 'dados'))
const args = chromeLoginArgs({
  profileDir,
  pjeUrl: 'https://pje.tjdft.jus.br',
  sistjUrl: 'https://sistj.tjdft.jus.br/sistj/sistj',
  remoteDebuggingPort: 9222,
})

assert(profileDir.endsWith(path.join('dados', 'chrome-login')), 'perfil Chrome deve ficar dentro da pasta de dados')
assert(args.includes('--remote-debugging-address=127.0.0.1'), 'Chrome deve expor CDP apenas localmente')
assert(args.includes('--remote-debugging-port=9222'), 'Chrome deve usar porta CDP padrao 9222')
assert(args.includes(`--user-data-dir=${profileDir}`), 'Chrome deve usar perfil dedicado do SOG')
assert(args.includes('--new-window'), 'Chrome deve abrir janela dedicada para login')
assert(args.includes('https://pje.tjdft.jus.br'), 'Chrome deve abrir PJe')
assert(args.includes('https://sistj.tjdft.jus.br/sistj/sistj'), 'Chrome deve abrir SISTJWEB')

const fakeExists = (candidate) => candidate.includes('Google Chrome') || candidate.endsWith('chrome.exe')
const chrome = findChromeExecutable({
  platform: 'win32',
  env: {
    LOCALAPPDATA: path.join('C:', 'Users', 'Carlos', 'AppData', 'Local'),
    PROGRAMFILES: path.join('C:', 'Program Files'),
    'PROGRAMFILES(X86)': path.join('C:', 'Program Files (x86)'),
  },
  exists: fakeExists,
})

assert(chrome.endsWith(path.join('Google', 'Chrome', 'Application', 'chrome.exe')), 'deve localizar Google Chrome no Windows')

const linuxMissing = findChromeExecutable({
  platform: 'linux',
  env: { PATH: path.join('/usr', 'bin') },
  exists: () => false,
})
assert(linuxMissing === null, 'deve retornar null quando Chrome nao existir no PATH')

const linuxChrome = findChromeExecutable({
  platform: 'linux',
  env: { PATH: [path.join('/opt', 'bin'), path.join('/usr', 'bin')].join(path.delimiter) },
  exists: (candidate) => candidate === path.join('/usr', 'bin', 'google-chrome'),
})
assert(linuxChrome === path.join('/usr', 'bin', 'google-chrome'), 'deve localizar Chrome no PATH')

console.log('chrome-login-verification=ok')
