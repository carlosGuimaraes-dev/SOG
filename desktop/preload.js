const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('sogDesktop', {
  paths: () => ipcRenderer.invoke('sog:paths'),
  configurationStatus: () => ipcRenderer.invoke('sog:configuration-status'),
  defaultConfig: () => ipcRenderer.invoke('sog:default-config'),
  loadConfig: () => ipcRenderer.invoke('sog:load-config'),
  checkDocker: () => ipcRenderer.invoke('sog:check-docker'),
  installDockerGuide: () => ipcRenderer.invoke('sog:install-docker-guide'),
  openDockerDesktop: () => ipcRenderer.invoke('sog:open-docker-desktop'),
  chooseDataDir: (currentPath) => ipcRenderer.invoke('sog:choose-data-dir', currentPath),
  saveConfig: (input) => ipcRenderer.invoke('sog:save-config', input),
  startStack: () => ipcRenderer.invoke('sog:start-stack'),
  restartStack: () => ipcRenderer.invoke('sog:restart-stack'),
  stopStack: () => ipcRenderer.invoke('sog:stop-stack'),
  healthcheck: () => ipcRenderer.invoke('sog:healthcheck'),
  startAgent: () => ipcRenderer.invoke('sog:start-agent'),
  testChromiumLogin: () => ipcRenderer.invoke('sog:test-chromium-login'),
  stopAgent: () => ipcRenderer.invoke('sog:stop-agent'),
  agentStatus: () => ipcRenderer.invoke('sog:agent-status'),
  collectDiagnostics: () => ipcRenderer.invoke('sog:collect-diagnostics'),
  openDashboard: () => ipcRenderer.invoke('sog:open-dashboard'),
})
