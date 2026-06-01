# Issues de implementacao: SOG Desktop

1. App Electron base com preflight, configuracao, status e diagnostico.
2. Orquestrador Docker no Electron para detectar Docker Desktop, subir/parar
   `docker-compose.desktop.yml` e validar healthchecks.
3. Compose de usuario final sem container `agente`, preservando volume local
   `dados`.
4. Empacotamento Windows do agente como `sog-agent.exe` via PyInstaller, com
   Chromium Playwright em `desktop/vendor/ms-playwright`, usando
   `desktop/scripts/prepare-python-runtime.ps1`.
5. Supervisao do processo local `agente/src/servico.py` pelo Electron.
6. Wizard grafico para gerar `.env.api` e `.env.agente` sem credenciais de
   PJe/SISTJWEB.
7. Mensagens do dashboard/API ajustadas para o modelo de agente desktop.
8. Fluxo de login por Chromium local visivel usando `PJE_URL` e `SISTJ_URL`.
9. Diagnostico exportavel com mascaramento de segredos e identificadores.
10. Smoke manual em Windows 11 limpo: Docker ausente, Docker parado, stack
    online, agente desktop, login e preservacao de dados.
