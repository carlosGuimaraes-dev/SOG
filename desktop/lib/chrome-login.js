const fs = require('node:fs')
const path = require('node:path')

const DEFAULT_CHROME_DEBUG_PORT = 9222

function chromeLoginProfileDir(dataDir) {
  return path.join(dataDir, 'chrome-login')
}

function chromeLoginArgs({ profileDir, pjeUrl, sistjUrl, remoteDebuggingPort = DEFAULT_CHROME_DEBUG_PORT }) {
  return [
    '--remote-debugging-address=127.0.0.1',
    `--remote-debugging-port=${remoteDebuggingPort}`,
    `--user-data-dir=${profileDir}`,
    '--new-window',
    pjeUrl,
    sistjUrl,
  ]
}

function findChromeExecutable({ platform = process.platform, env = process.env, exists = fs.existsSync } = {}) {
  const candidates = []

  if (platform === 'win32') {
    for (const root of [env.LOCALAPPDATA, env.PROGRAMFILES, env['PROGRAMFILES(X86)']]) {
      if (root) candidates.push(path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'))
    }
  } else if (platform === 'darwin') {
    candidates.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
  } else {
    candidates.push('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser')
  }

  for (const candidate of candidates) {
    const absolute = platform === 'win32' ? path.win32.isAbsolute(candidate) : path.isAbsolute(candidate)
    if (absolute && exists(candidate)) {
      return candidate
    }
    if (!absolute) {
      const resolved = findOnPath(candidate, env, exists)
      if (resolved) return resolved
    }
  }

  return null
}

function findOnPath(command, env, exists) {
  const pathValue = env.PATH || ''
  for (const dir of pathValue.split(path.delimiter)) {
    if (!dir) continue
    const candidate = path.join(dir, command)
    if (exists(candidate)) return candidate
  }
  return null
}

module.exports = {
  DEFAULT_CHROME_DEBUG_PORT,
  chromeLoginArgs,
  chromeLoginProfileDir,
  findChromeExecutable,
}
