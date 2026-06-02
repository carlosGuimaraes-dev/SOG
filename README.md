# SOG

Sistema para controlar e emitir guias finais de custas processuais no TJDFT.
O repositório combina:

- `agente/`: automação Python/Playwright para PJe, SISTJWEB e integrações auxiliares
- `api/`: backend FastAPI do dashboard operacional
- `frontend/`: dashboard React para login, fila, detalhe, histórico e ciclo atual
- `shared/`: acesso compartilhado ao SQLite e contratos comuns
- `nginx/`: ponto de entrada HTTP do Compose
- `desktop/`: instalador/app Electron para operadores leigos, com Docker guiado
  e agente Playwright local

## Estado atual

O dashboard já controla o agente por API e SQLite, com suporte a:

- autenticação por cookies `httpOnly`
- comandos `iniciar` e `parar` do agente
- acompanhamento de ciclo atual e último ciclo
- reprocessamento de processos elegíveis
- screenshot autenticado por processo
- fila, detalhe e histórico no frontend

O caminho recomendado para usuario final e o SOG Desktop:

- API, frontend e nginx rodam em Docker Desktop;
- o agente Playwright roda fora do container para abrir Chromium visivel;
- PJe e SISTJWEB continuam com login manual por SSO/2FA, sem armazenar senha;
- `docker-compose.desktop.yml` remove o container `agente` do fluxo de usuario
  final e preserva os dados em `%LOCALAPPDATA%/SOG/dados`.

## Instalar no Windows com npx

Este e o caminho recomendado para instalar o iSOG/SOG Desktop em uma maquina
Windows de usuario final. O comando `npx` baixa e abre o instalador oficial; o
instalador configura o aplicativo local, que sobe o sistema em containers Docker
e abre o dashboard no navegador.

### Requisitos do usuario

- Windows 11 com acesso de usuario para instalar aplicativos.
- Internet liberada para baixar o instalador, Docker Desktop e imagens Docker.
- Node.js LTS instalado, para disponibilizar o comando `npx`.
- Docker Desktop instalado ou permissao para instala-lo durante o assistente do
  iSOG/SOG Desktop.
- Chrome instalado se o usuario quiser usar o dashboard especificamente no
  Chrome. Por padrao, o aplicativo abre o navegador padrao do Windows.

### Passo a passo

1. Abra o PowerShell no Windows.
2. Execute:

   ```powershell
   npx -y sogtj
   ```

3. Aguarde o download e a abertura do instalador do iSOG/SOG Desktop.
4. Siga o assistente de instalacao e mantenha a criacao do atalho quando
   oferecida.
5. Abra o iSOG/SOG Desktop pelo Menu Iniciar ou pelo atalho criado.
6. Se o Docker Desktop ainda nao estiver instalado, use a acao indicada pelo
   aplicativo para instalar o Docker Desktop. Depois da instalacao, abra o
   Docker Desktop e aguarde ele ficar em execucao.
7. No iSOG/SOG Desktop, confirme as configuracoes iniciais e inicie a stack do
   sistema.
8. O aplicativo subira os containers Docker locais do SOG, incluindo API,
   frontend e nginx.
9. Quando a stack estiver pronta, o dashboard sera aberto no navegador padrao em
   `http://localhost` ou na porta configurada no assistente.
10. Se quiser usar o Chrome e ele nao abrir automaticamente, defina o Chrome
    como navegador padrao do Windows ou copie a URL do dashboard para o Chrome.

Os dados locais do usuario ficam em `%LOCALAPPDATA%/SOG/dados`. O dashboard e a
API rodam localmente dentro dos containers Docker; o agente Playwright roda pelo
aplicativo desktop para permitir login manual nos sistemas externos quando
necessario.

## Documentação canônica

- [docs/README.md](docs/README.md): mapa da documentação e classificação de artefatos históricos
- [docs/architecture.md](docs/architecture.md): componentes, fluxo e persistência
- [docs/api.md](docs/api.md): autenticação, rotas principais e estados
- [docs/distribuicao-npx-sogtj.md](docs/distribuicao-npx-sogtj.md): distribuição do iSOG via `npx`
- [docs/operacao-local-docker.md](docs/operacao-local-docker.md): execução local em Docker e limitações
- [docs/instalador-desktop.md](docs/instalador-desktop.md): instalador gráfico, runtime desktop e fluxo do operador
- [frontend/README.md](frontend/README.md): visão do dashboard e experiência atual de frontend

## Requisitos

- Docker e Docker Compose
- Node.js 20+ para desenvolvimento local do frontend
- Python 3.12+ para desenvolvimento local da API ou do agente

## Configuração

O projeto usa dois arquivos de ambiente:

- `.env.api`: configura o serviço FastAPI
- `.env.agente`: configura a automação e integrações do agente

Crie ambos a partir de `.env.example`:

```bash
cp .env.example .env.api
cp .env.example .env.agente
```

Revise os blocos correspondentes dentro do próprio `.env.example` antes de subir
o Compose. Em especial:

- No SOG Desktop, preencha a senha normal no instalador; ele gera
  `DASHBOARD_SENHA_HASH` automaticamente.
- Em execução manual fora do instalador, `DASHBOARD_SENHA_HASH` precisa ser um
  hash bcrypt válido.
- `JWT_SECRET_KEY` precisa ter pelo menos 32 caracteres
- PJe e SISTJWEB usam login interativo; não há usuário/senha desses sistemas no `.env`
- Telegram é tratado como obrigatório para homologação local do agente

Para gerar o hash bcrypt apenas em execução manual:

```bash
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('sua_senha'))"
```

## Subir com Docker

Produção local:

```bash
docker-compose up -d --build
```

Usuario final Windows 11:

```powershell
cd desktop
npm install
npm run build:win
```

O instalador gerado abre uma interface grafica para configurar o SOG, guiar a
instalacao do Docker Desktop quando ausente, subir a stack e iniciar o agente
local. A interface tambem permite reiniciar a stack Docker e mudar a porta do
dashboard quando a porta 80 estiver ocupada.

Desenvolvimento:

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

URLs úteis:

| Ambiente | URL | Observação |
|---|---|---|
| Compose principal | <http://localhost> | entrada via nginx |
| Compose principal | <http://localhost/api/v1/health> | health da API via nginx |
| Compose dev | <http://localhost:8080> | nginx dev |
| Compose dev | <http://localhost:3001> | frontend Vite |

## Fluxo operacional resumido

1. O operador acessa o dashboard e faz login.
2. O frontend consulta `/api/v1/auth/me` e as rotas operacionais via cookies.
3. O dashboard envia comandos para `/api/v1/agente/iniciar` ou `/api/v1/agente/parar`.
4. A API grava o controle no SQLite compartilhado.
5. O agente processa ciclos, filas e tarefas assíncronas, atualizando tabelas de
   `processos`, `agente_controle`, `agente_ciclos`, `agente_ciclo_membros` e
   `tarefas`.

## Desenvolvimento fora do Docker

API:

```bash
cd api
pip install -r requirements.txt
pip install -e ../shared
uvicorn src.app:app --reload --port 8000
```

Agente:

```bash
cd agente
pip install -r requirements.txt
pip install -e ../shared
playwright install chromium
python src/servico.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
pytest agente/tests/ api/tests/ -v
cd frontend && npm test
```

## Limites e ambiguidades já conhecidas

- `docs/regras_custas_tjdft.md` é um template de coleta manual, não uma verdade homologada de regra de negócio.
- `docs/PRD.md` e `SYMPHONY.md` permanecem como artefatos de origem/histórico.
- A persistência do `storage_state` do Playwright não está descrita de forma consistente entre código e Compose; veja a nota em `docs/operacao-local-docker.md`.
