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
- **Infra**: Docker Compose + Nginx + Ubuntu VPS

## Requisitos

- Docker + Docker Compose
- Node.js 20+ (para dev local do frontend)
- Python 3.12+ (para dev local do agente/API)

## Setup

### 1. Clone e configure

```bash
git clone git@github.com:carlosGuimaraes-dev/SOG.git
cd SOG
cp .env.example .env
# Edite .env com as chaves de serviço necessárias
```

### 2. Variáveis de ambiente (.env)

```env
# PJE
PJE_URL=https://pje.tjdft.jus.br/...
PJE_ETIQUETA=SHEILA DE DEUS (TREINAMENTO)

# SISTJWEB
SISTJ_URL=https://sistj.tjdft.jus.br/sistj/sistj

# Datajud API
DATAJUD_API_KEY=sua_chave
DATAJUD_URL=https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search

# Dashboard
DASHBOARD_USUARIO=admin
DASHBOARD_SENHA_HASH=$2b$12$...  # bcrypt hash

# Notificação (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORTA=587
SMTP_USUARIO=...
SMTP_SENHA=...
EMAIL_DESTINO=...
```

PJE e SISTJWEB usam SSO com 2FA. O agente abre um navegador visível quando a
sessão expira; o usuário faz o login manualmente e o sistema salva o
`storage_state` para reutilizar a sessão. Não configure usuário ou senha desses
sistemas em arquivos `.env`.

> Para gerar o hash bcrypt: `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('sua_senha'))"`

### 3. Dev Local (sem Docker)

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

### Docker (Produção)

```bash
docker-compose up -d --build
```

### Docker Dev (Hot reload)

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

| Serviço | URL |
|---------|-----|
| Dashboard | http://localhost |
| API direta | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

### Login

Como o `DASHBOARD_SENHA_HASH` no `.env` está com placeholder inválido, o sistema entra em **modo desenvolvimento**:

- **Usuário:** `admin`
- **Senha:** qualquer coisa

> Para definir uma senha real, gere o hash:  
> `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('sua_senha'))"`  
> e cole no `.env` como `DASHBOARD_SENHA_HASH`.

### Comandos úteis

```bash
# Ver status dos containers
docker-compose -f docker-compose.dev.yml ps

# Logs em tempo real
docker-compose -f docker-compose.dev.yml logs -f api

# Parar tudo
docker-compose -f docker-compose.dev.yml down

# Rebuildar só a API
docker-compose -f docker-compose.dev.yml up -d --build api
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

## Estrutura

```
SOG/
├── agente/              # Automação Playwright
│   ├── src/
│   │   ├── main.py
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
└── .env
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

1. **Agente** (cron horário) coleta processos do PJE
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
