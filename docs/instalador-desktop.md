# SOG Desktop: instalador grafico e agente local

O SOG Desktop e o caminho para usuarios finais leigos em Windows 11. Ele evita
comandos de terminal, guia a instalacao do Docker Desktop e executa o agente
Playwright fora do container para permitir login interativo em Chromium visivel.

## Arquitetura

- `desktop/`: app Electron, wizard de configuracao, preflight, status e diagnostico.
- `docker-compose.desktop.yml`: stack de usuario final sem container `agente`.
- Docker Desktop: executa `api`, `frontend` e `nginx`.
- Imagens Docker: o Compose aceita `SOG_API_IMAGE` e `SOG_FRONTEND_IMAGE` para
  puxar imagens prepublicadas; se nao forem informadas, usa build local como
  fallback de desenvolvimento.
- Agente local: o Electron inicia `agente/src/servico.py` com Python/Playwright
  empacotado no instalador Windows.
- Dados persistentes: `%LOCALAPPDATA%/SOG/dados`, montado como `/dados` na API e
  usado diretamente pelo agente local.

## Fluxo do operador

1. Abrir o SOG Desktop.
2. Se Docker Desktop nao estiver instalado, clicar em `Instalar Docker Desktop`.
3. Preencher a configuracao inicial.
4. Clicar em `Subir Docker`.
5. Clicar em `Iniciar agente`.
6. Abrir o dashboard em `http://localhost` ou na porta configurada no wizard.
7. Ao iniciar um ciclo, o agente abre Chromium local para login manual em PJe e
   SISTJWEB quando a sessao estiver ausente ou expirada.

Antes de rodar um ciclo real, `Testar Chromium` abre uma janela visivel com PJe
e SISTJWEB por alguns segundos. Use esse teste para confirmar que o Chromium
local empacotado consegue abrir as paginas corretas.

Se a stack local precisar ser recriada, use `Reiniciar Docker` no proprio SOG
Desktop. O operador final nao precisa abrir terminal para subir, parar ou
reiniciar os containers.

O SOG nao armazena usuario ou senha de PJe/SISTJWEB. O login permanece manual
por SSO/2FA e o agente salva apenas `storage_state`.

No campo `Pasta de dados`, use `Escolher pasta` para selecionar graficamente o
diretorio persistente. Essa pasta e preservada em reinstalacao/upgrade e e
compartilhada entre agente local e containers Docker.

Enquanto o SOG Desktop estiver aberto, o status e rechecado automaticamente.
Depois que o operador instala ou abre o Docker Desktop, a tela volta a mostrar
`Docker Desktop pronto` assim que o Docker ficar saudavel, sem exigir terminal.

O preflight considera a configuracao pendente enquanto arquivos ou campos
obrigatorios estiverem ausentes. Isso inclui URLs PJe/SISTJWEB, segredo do
dashboard, Datajud, Telegram, pasta de dados, arquivo de ambiente da API para o
Docker e uma porta HTTP valida.

## Build Windows

No Windows 11 com Node.js, Python 3.12 e Docker Desktop instalados:

```powershell
cd desktop
npm install
npm run build:win
```

O script `prepare:python:win` cria um ambiente temporario de build, gera
`desktop/vendor/agent/sog-agent.exe` com PyInstaller, instala Chromium do
Playwright em `desktop/vendor/ms-playwright` e inclui esses artefatos no
instalador NSIS gerado pelo Electron Builder. Depois de gerar o executavel, o
build executa `sog-agent.exe --desktop-smoke` para validar imports, Playwright
e Chromium headless antes de produzir o instalador final.

O workflow `.github/workflows/sog-desktop-windows.yml` e o gate automatizado de
build: ele roda em `windows-latest`, executa `npm run build:win`, valida o
runtime empacotado com `npm run verify:packed-runtime`, valida o instalador
`.exe` com `npm run verify:win-artifact` e publica o artefato. O proprio
`build:win` tambem executa essas validacoes para que o comando local seja
autocontido. O workflow tambem executa `smoke:upgrade` em uma pasta temporaria
do runner e publica um resumo de evidencias no `GITHUB_STEP_SUMMARY`.

O workflow `.github/workflows/sog-desktop-images.yml` publica imagens de API e
frontend no GHCR. Para uma distribuicao final sem build Docker na maquina do
operador, informe as imagens nos campos avancados `Imagem Docker API` e
`Imagem Docker Frontend` do SOG Desktop, usando `Politica de pull = always`.

Se a porta 80 estiver ocupada na maquina, altere `Porta HTTP do dashboard` no
wizard. O app passa a abrir e checar `http://localhost:<porta>`.

Para auditar a cobertura estatica do plano do instalador, rode:

```powershell
cd desktop
npm run verify:plan
```

Esse comando valida os artefatos locais e lista separadamente as evidencias que
dependem de Windows 11 real.

## Smoke Windows

Depois de instalar e configurar o SOG Desktop em Windows 11, o smoke pode rodar
no checkout de build ou contra a instalacao gerada pelo NSIS:

```powershell
cd desktop
npm run smoke:win
```

O smoke valida Docker, Compose, arquivos de configuracao, dashboard, API,
executavel do agente e Chromium Playwright, respeitando a porta configurada em
`SOG_HTTP_PORT`. A confirmacao do login ainda e manual: iniciar o agente pelo
SOG Desktop, iniciar um ciclo e verificar se Chromium abre PJe/SISTJWEB.

Para validar preservacao em reinstalacao/upgrade:

```powershell
cd desktop
npm run smoke:upgrade -- --Mode baseline
# reinstale ou atualize o SOG Desktop no mesmo usuario Windows
npm run smoke:upgrade -- --Mode verify
```

Esse smoke cria/mede sentinelas em `custas.db`, `auth/pje_storage.json`,
`auth/sistj_storage.json`, PDFs e screenshots, e falha se qualquer arquivo
sumir ou mudar apos o upgrade.

Este smoke e operacional: ele exige Docker Desktop rodando e o SOG ja
configurado. O GitHub Actions valida o build do instalador; a maquina do
operador valida Docker Desktop, dashboard e login visivel.

## Diagnostico

O botao `Gerar diagnostico` grava uma pasta datada em `%LOCALAPPDATA%/SOG/logs`
com `diagnostico.json` e, quando existir, `agente-ultimas-linhas.log`. O pacote
inclui status de Docker, API, dashboard, agente, Compose e o trecho final do log
mais recente do agente. O conteudo mascara segredos comuns, hash/sigilo do
dashboard, CPF, numero CNJ e caminhos locais que possam revelar o nome do
usuario antes de gravar. Ao finalizar, o SOG Desktop abre a pasta do pacote para
facilitar envio ao suporte.
