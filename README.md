# SOG — Sistema de Ordem de Guias (Custas Processuais TJDFT)

Sistema automatizado para extração, preenchimento e emissão de guias de custas processuais no TJDFT. Integra PJE, SISTJWEB e API Datajud (CNJ) com dashboard de aprovação humana.

## Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agente    │────▶│   API       │◀────│  Frontend   │
│  (Python)   │     │  (FastAPI)  │     │  (React)    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   PJE/SISTJWEB        SQLite            Nginx
   Datajud CNJ      (shared vol)       (proxy/ssl)
```

## Stack

- **Agente**: Python 3.12 + Playwright (automação PJE/SISTJWEB)
- **API**: FastAPI + JWT Auth + SQLite
- **Frontend**: React 18 + Tailwind CSS + Vite
- **Infra**: Docker Compose local + Nginx

## Requisitos

- Docker + Docker Compose
- Node.js 20+ (apenas para desenvolvimento fora do Docker)
- Python 3.12+ (apenas para desenvolvimento/testes fora do Docker)

## Setup

### 1. Clone e configure

```bash
git clone git@github.com:carlosGuimaraes-dev/SOG.git
cd SOG
./scripts/prepare-runtime.sh
python3 ./scripts/prepare-internal-runtime.py
# Edite .env.api e .env.agente com as chaves de serviço necessárias
./scripts/start-local.sh
```

### 2. Variáveis de ambiente

O runtime em Docker usa dois arquivos separados:

- `.env.api` para API/dashboard
- `.env.agente` para automação, integrações externas e notificações

```env
# .env.agente — PJE
PJE_URL=https://pje.tjdft.jus.br/...
PJE_ETIQUETA=SHEILA DE DEUS (TREINAMENTO)

# .env.agente — SISTJWEB
SISTJ_URL=https://sistj.tjdft.jus.br/sistj/sistj

# .env.agente — Datajud API
DATAJUD_API_KEY=sua_chave
DATAJUD_URL=https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search

# .env.api — Dashboard
DASHBOARD_USUARIO=admin
DASHBOARD_SENHA_HASH=$2b$12$...  # bcrypt hash

# .env.api — JWT
JWT_SECRET_KEY=change-me-in-production-min-32-chars-long-key

# .env.agente — Notificação
SMTP_HOST=smtp.gmail.com
SMTP_PORTA=587
SMTP_USUARIO=...
SMTP_SENHA=...
EMAIL_DESTINO=...
```

PJE e SISTJWEB usam SSO com 2FA. O agente abre um navegador visível quando a
sessão expira; o usuário faz o login manualmente e o sistema salva o
`storage_state` para reutilizar a sessão. Não configure usuário ou senha desses
sistemas em arquivos `.env.agente`.

> Para gerar o hash bcrypt: `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('sua_senha'))"`

### 3. Operação local em Docker

O modo operacional alvo é local e totalmente containerizado. O agente roda como
serviço longo dentro do Docker Compose, sem cron e sem VPS.

Fluxo esperado:

1. Subir o Compose.
2. Acessar o dashboard.
3. Clicar em **Iniciar Agente**.
4. O agente abre um navegador interativo containerizado para SSO/2FA do PJe e
   SISTJWEB.
5. Após o login manual, o agente salva `storage_state` em volume persistente e
   inicia o trabalho.

Detalhes: [docs/operacao-local-docker.md](docs/operacao-local-docker.md).

### 4. Dev Local (sem Docker)

**API + Agente:**

```bash
cd agente
pip install -r requirements.txt
playwright install chromium

cd ../api
pip install -r requirements.txt
uvicorn src.app:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Subir o Projeto

### Docker (Produção local)

Prefira o wrapper operacional, que prepara o runtime, grava o diagnóstico em
`dados/support/runtime-diagnostic.json` e interrompe com mensagem simples de
suporte quando detectar falhas bloqueantes:

```bash
./scripts/start-local.sh
```

Para o preparo HITL das dependências do host, rode:

```bash
python3 ./scripts/prepare-internal-runtime.py
```

Esse fluxo:

- relata Node.js, npm, Docker CLI e WSL como presentes/ausentes
- valida pré-requisitos antes do `docker compose up` sem exigir containers já iniciados
- pede autorização antes de continuar quando houver dependências faltantes
- explica a etapa elevada antes de qualquer UAC do WSL
- persiste `dados/support/runtime-preparation-state.json` para retomada após reboot

Para rodar o preparo/startup sem prompt interativo, forneça a autorização no
ambiente:

```bash
SOG_RUNTIME_PREP_AUTHORIZATION=approved ./scripts/start-local.sh
```

Execução direta continua disponível:

```bash
docker compose up -d --build
```

### Docker Dev (Hot reload)

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

| Serviço | URL |
|---------|-----|
| Dashboard | <http://localhost> |
| API direta | <http://localhost:8000> |
| Swagger | <http://localhost:8000/docs> |

### Login

Como o `DASHBOARD_SENHA_HASH` no `.env.api` está com placeholder inválido, o sistema entra em **modo desenvolvimento**:

- **Usuário:** `admin`
- **Senha:** qualquer coisa

> Para definir uma senha real, gere o hash:  
> `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('sua_senha'))"`  
> e cole no `.env.api` como `DASHBOARD_SENHA_HASH`.

### Comandos úteis

```bash
# Ver status dos containers
docker compose -f docker-compose.dev.yml ps

# Logs em tempo real
docker compose -f docker-compose.dev.yml logs -f api

# Parar tudo
docker compose -f docker-compose.dev.yml down

# Rebuildar só a API
docker compose -f docker-compose.dev.yml up -d --build api
```

## Testes

```bash
# Todos os testes
pytest agente/tests/ api/tests/ -v

# Apenas agente
pytest agente/tests/ -v

# Apenas API
pytest api/tests/ -v
```

Para validar o `extrator_pdf` com PyMuPDF real em runtime reproduzível, prefira
o container de QA:

```bash
./scripts/qa-extrator-pdf.sh
```

## Playwright no runtime Paperclip

Para diagnosticar e abrir o Chromium cacheado no runtime Paperclip, use:

```bash
./scripts/playwright-runtime.sh
./scripts/playwright-runtime.sh https://example.com
```

Para smoke headless alinhado ao runtime atual, prefira:

```bash
npx playwright screenshot --browser=chromium 'data:text/html,<title>SOG smoke</title><h1>ok</h1>' /tmp/sog-smoke.png
```

Se o container Paperclip estiver sem as bibliotecas Linux exigidas pelo
Chromium, o script falha com a lista exata de `.so` ausentes e os pacotes
Debian/Ubuntu esperados. Detalhes e estado atual em
`docs/paperclip-playwright-runtime.md`.

## Estrutura

```text
SOG/
├── agente/              # Automação Playwright
│   ├── src/
│   │   ├── servico.py
│   │   ├── config.py
│   │   ├── regras.py
│   │   ├── modulos/
│   │   │   ├── pje.py
│   │   │   ├── sistjweb.py
│   │   │   ├── datajud.py
│   │   │   ├── extrator_pdf.py
│   │   │   ├── extrator_sentenca.py
│   │   │   ├── parser.py
│   │   │   ├── emissor.py
│   │   │   ├── retry.py
│   │   │   └── selectors.py
│   │   └── banco/
│   │       ├── db.py
│   │       └── schema.sql
│   └── tests/
│       ├── test_datajud.py
│       ├── test_extrator_pdf.py
│       ├── test_parser.py
│       └── test_regras.py
├── api/                 # FastAPI + JWT
│   ├── src/
│   │   ├── app.py
│   │   ├── auth.py
│   │   └── rotas/
│   │       ├── auth.py
│   │       ├── processos.py
│   │       ├── aprovacao.py
│   │       └── historico.py
│   └── tests/
│       └── test_api.py
├── frontend/            # React + Tailwind
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── auth.tsx
│   │   ├── components/ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Skeleton.tsx
│   │   ├── hooks/
│   │   │   └── useToast.ts
│   │   └── pages/
│   │       ├── Login.tsx
│   │       ├── Fila.tsx
│   │       ├── Detalhe.tsx
│   │       └── Historico.tsx
├── nginx/
│   ├── nginx.conf
│   └── nginx-dev.conf
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.api
└── .env.agente
```

## API Endpoints

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| POST | `/auth/login` | Público | Login JWT |
| POST | `/auth/refresh` | Público | Refresh token |
| GET | `/health` | Público | Health check |
| GET | `/processos` | JWT | Lista pendentes |
| GET | `/processos/{id}` | JWT | Detalhes |
| POST | `/aprovar/{id}` | JWT | Aprova e emite |
| POST | `/rejeitar/{id}` | JWT | Rejeita com obs |
| GET | `/historico` | JWT | Histórico paginado |

## Fluxo de Trabalho

1. **Agente** (serviço longo iniciado pelo dashboard) coleta processos do PJE
2. Para cada processo: consulta Datajud + extrai documentos + extrai custas iniciais do PDF + preenche SISTJWEB
3. Status → `aguardando_aprovacao`
4. **Operador** revisa no dashboard e clica **Aprovar** ou **Rejeitar**
5. Ao aprovar: agente emite PDF e anexa no PJE
6. Status → `emitido`

## Segurança

- `.env` nunca deve ser commitado
- JWT com refresh tokens
- Senhas armazenadas com bcrypt
- Screenshots em `/dados/screenshots/` (volume Docker)

## Licença

Uso interno.
