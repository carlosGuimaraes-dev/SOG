# PRD.md — Pipeline de Custas Processuais TJDFT

> Status deste arquivo: artefato histórico de origem.
> Não use este documento como espelho fiel do runtime atual sem validar contra o
> código e contra os docs canônicos em `README.md`, `docs/architecture.md`,
> `docs/api.md` e `docs/operacao-local-docker.md`.

> Documento de referência completo para implementação via Claude Code.
> Leia integralmente antes de escrever qualquer linha de código.

---

## 1. VISÃO GERAL

Sistema automatizado que:

1. Monitora (cron horário) a pasta de uma contadora no PJE/TJDFT
2. Para cada processo novo: extrai dados via API Datajud + Playwright
3. Preenche a planilha de custas no SISTJWEB
4. Aguarda aprovação humana via dashboard React
5. Após aprovação: emite o Demonstrativo e o anexa no PJE

**Stack:**

- Python 3.12 + Playwright (agente)
- FastAPI (API do dashboard)
- React + shadcn/ui (frontend dashboard)
- SQLite (banco de dados)
- Docker + Docker Compose (infraestrutura)
- VPS Linux Ubuntu 24 LTS
- Nginx + Cloudflare (proxy reverso + SSL)

---

## 2. ARQUITETURA DE CONTAINERS

```tree
docker-compose.yml
├── agente        (Python + Playwright + cron)
├── api           (FastAPI)
├── frontend      (React + shadcn/ui — build estático servido pelo nginx)
├── nginx         (proxy reverso + SSL)
└── volume: ./dados/custas.db  (SQLite compartilhado entre agente e api)
```

### Portas internas

| Container | Porta |
|---|---|
| api (FastAPI) | 8000 |
| frontend | 3000 |
| nginx (externo) | 80 / 443 |

---

## 3. ESTRUTURA DE PASTAS

```tree
custas-pipeline/
├── docker-compose.yml
├── .env                        # nunca commitar
├── .gitignore
├── CLAUDE.md                   # este arquivo
│
├── agente/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── crontab                 # "0 * * * * python /app/src/main.py"
│   └── src/
│       ├── main.py             # orquestrador principal
│       ├── config.py           # lê variáveis de ambiente
│       ├── regras.py           # tabela de combinações por área/tipo
│       ├── modulos/
│       │   ├── pje.py          # login, pasta, documentos, anexo
│       │   ├── datajud.py      # API CNJ
│       │   ├── parser.py       # extração por regex/tipo de doc
│       │   ├── sistjweb.py     # preenchimento da planilha
│       │   └── emissor.py      # gravar e aprovar + download PDF
│       ├── banco/
│       │   ├── db.py           # conexão e queries SQLite
│       │   └── schema.sql      # estrutura das tabelas
│       └── utils/
│           ├── logger.py
│           └── notificador.py  # alerta por email quando há pendente
│
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── app.py              # FastAPI main
│       └── rotas/
│           ├── processos.py    # GET /processos, GET /processos/{id}
│           ├── aprovacao.py    # POST /aprovar/{id}, POST /rejeitar/{id}
│           └── historico.py    # GET /historico
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── Fila.tsx        # lista de processos pendentes
│       │   ├── Detalhe.tsx     # revisão de um processo
│       │   └── Historico.tsx
│       └── components/
│           ├── ProcessoCard.tsx
│           ├── CamposRevisao.tsx
│           └── BotoesAcao.tsx
│
├── nginx/
│   └── nginx.conf
│
└── dados/
    └── custas.db               # criado automaticamente
```

---

## 4. VARIÁVEIS DE AMBIENTE (.env)

```env
# PJE
PJE_URL=https://pje.tjdft.jus.br/...
PJE_ETIQUETA=SHEILA DE DEUS (TREINAMENTO)

# SISTJWEB
SISTJ_URL=https://sistj.tjdft.jus.br/sistj/sistj

# Datajud API
DATAJUD_API_KEY=
DATAJUD_URL=https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search

# Dashboard
DASHBOARD_USUARIO=admin
DASHBOARD_SENHA=

# Notificação
SMTP_HOST=
SMTP_PORTA=587
SMTP_USUARIO=
SMTP_SENHA=
EMAIL_DESTINO=
```

---

## 5. SCHEMA DO BANCO (SQLite)

```sql
CREATE TABLE IF NOT EXISTS processos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    numero_sem_mascara TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente',
    -- status: pendente | aguardando_aprovacao | aprovado | rejeitado | emitido | erro | pendente_manual
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    tentativas INTEGER DEFAULT 0,
    erro_msg TEXT
);

CREATE TABLE IF NOT EXISTS dados_processo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER REFERENCES processos(id),
    instancia TEXT,
    processo_eletronico INTEGER DEFAULT 1,
    circunscricao TEXT,
    competencia TEXT,
    feito TEXT,
    classe TEXT,
    valor_causa TEXT,
    valor_causa_atualizado TEXT,
    data_distribuicao TEXT,
    polo_ativo TEXT,
    polo_passivo TEXT,
    tipo_guia TEXT,
    pro_rata INTEGER DEFAULT 0,
    sucumbentes TEXT,         -- JSON array
    ids_oficios TEXT,
    ids_alvaras TEXT,
    ids_traslados TEXT,
    ids_mandados TEXT,
    ids_cartas_sentenca TEXT,
    ids_ar TEXT,
    ids_armp TEXT,
    ids_circunscricao_origem TEXT,
    ids_outra_circunscricao TEXT,
    outros_itens TEXT,        -- JSON array
    compensacao TEXT,         -- JSON array
    custas_pagas TEXT,        -- JSON array
    sucumbente_nome TEXT,
    sucumbente_cpf_cnpj TEXT,
    sucumbente_tipo TEXT,
    honorarios_percentual TEXT,
    suspensao_exigibilidade INTEGER DEFAULT 0,
    valor_total_recolher TEXT,
    area_direito TEXT,
    obs_operador TEXT,
    screenshot_path TEXT
);

CREATE TABLE IF NOT EXISTS documentos_pje (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER REFERENCES processos(id),
    doc_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    data_assinatura TEXT,
    nome TEXT
);

CREATE TABLE IF NOT EXISTS log_execucao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER REFERENCES processos(id),
    etapa TEXT NOT NULL,
    status TEXT NOT NULL,     -- ok | erro | aviso
    mensagem TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. FLUXO DETALHADO DO AGENTE

### 6.1 main.py — Orquestrador

```
1. Conectar ao SQLite
2. Chamar pje.coletar_lista_processos()
3. Para cada número recebido:
   a. Verificar se já existe no banco
   b. Se existe e status != 'erro': pular
   c. Se novo ou erro: iniciar pipeline
4. Pipeline por processo:
   a. datajud.consultar(numero)
   b. pje.coletar_documentos(numero)
   c. parser.processar(documentos)
   d. sistjweb.preencher(dados)
   e. status → 'aguardando_aprovacao'
   f. notificador.enviar_alerta()
5. Log de cada etapa
```

### 6.2 pje.py — Módulo PJE

#### Login

```
1. Navegar até PJE_URL
2. Se não houver sessão válida, abrir navegador visível
3. Usuário realiza SSO/2FA manualmente
4. Salvar storage_state após login bem-sucedido
5. Confirmar: nome do usuário visível no topo
6. Em timeout: solicitar nova autenticação interativa
```

#### Coleta da lista de processos

```
1. Meu Perfil → Núcleo Permanente de Cálculos
2. Tarefas → Incluir Cálculo
3. Etiquetas → rolar até PJE_ETIQUETA → clicar
4. Extrair todos os números de processo
```

#### Coleta de documentos

```
1. Clicar no número do processo
2. Ler tabela: Id | Data da Assinatura | Documento | Tipo
3. Salvar todos em documentos_pje
```

#### Leitura de conteúdo

```
Ler texto de:
- Tipo "Sentença" → dispositivo para parser
- Tipo "Decisão" → condenação em custas
- Tipo "Comprovante de Pagamento de Custas" → data, valor, nº guia
```

#### Anexar Demonstrativo

```
1. Voltar ao processo
2. Upload do PDF baixado do SISTJWEB
3. Confirmar anexo
```

### 6.3 datajud.py — API CNJ

```
Endpoint: POST DATAJUD_URL
Header: Authorization: APIKey {DATAJUD_API_KEY}

Campos extraídos:
- data_distribuicao   → hits._source.dataAjuizamento
- polo_ativo          → partes[tipo=AUTOR].nome
- polo_passivo        → partes[tipo=REU].nome (ou "Não Há")
- valor_causa         → hits._source.valorCausa
- classe              → hits._source.classe.nome

Detectar instância pelo número CNJ:
- Segmento TT (posição 14-15 do número sem máscara)
- "07" → 1ª Instância
- "08" → 2ª Instância
```

### 6.4 parser.py — Extração por tipo de documento

#### Mapeamento Tipo PJE → Campo SISTJWEB

| Tipo no PJE | Ação | Campo |
|---|---|---|
| Mandado | ID | ids_mandados |
| Ofício | ID | ids_oficios |
| Alvará | ID | ids_alvaras |
| Traslado | ID | ids_traslados |
| Carta de Sentença | ID | ids_cartas_sentenca |
| AR | ID | ids_ar |
| AR/MP | ID | ids_armp |
| Diligência | ID | ids_circunscricao_origem |
| Guia | ID | custas_pagas[].numero_guia |
| Comprovante de Pagamento de Custas | Ler conteúdo | custas_pagas[].data + valor |
| Sentença | Ler conteúdo | sucumbente + honorários + suspensão |
| Decisão | Ler conteúdo | verificar condenação |
| Certidão | Ignorar | — |
| Certidão de Disponibilização | Ignorar | — |
| Petição | Ignorar | — |
| Contestação | Ignorar | — |
| Demais | Ignorar | — |

#### IDs múltiplos

```python
# Separar por vírgula sem espaço
ids_mandados = ",".join([d.doc_id for d in docs if d.tipo == "Mandado"])
# Ex: "207553631,228187287"
```

#### Regex — Sentença

```python
# Sucumbente
r"condeno\s+(?:\w+\s+)?([A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇ][A-ZÁÉÍÓÚÃÕÀÂÊÎÔÛÇa-záéíóúãõàâêîôûç\s\.]+?)\s+ao\s+pagamento"

# Honorários
r"honorários[^%]+?(\d+(?:,\d+)?)\s*%"

# Suspensão de exigibilidade
r"art(?:igo)?\.?\s*98.{0,50}§\s*3"

# Valor da condenação
r"valor\s+d[ae]\s+condena[çc][ãa]o\s+de\s+R\$\s*([\d.,]+)"
```

#### Regex — Comprovante de Pagamento

```python
# Data
r"(?:data\s+d[eo]\s+pagamento|pago\s+em)[:\s]+(\d{2}/\d{2}/\d{4})"

# Valor
r"(?:valor\s+(?:pago|das\s+custas\s+pagas)|valor\s+recolhido)[:\s]+R?\$?\s*([\d.,]+)"

# Nº da Guia
r"(?:guia\s+n[º°\.]\s*|número\s+da\s+guia[:\s]+)(\d+)"
```

### 6.5 regras.py — Combinações por área do direito

```python
REGRAS_OUTROS_ITENS = {
    "civel_comum": [
        {"item_guia": "Distribuidor",  "item_calculo": "D-I-a",         "quantidade": 1},
        {"item_guia": "Distribuidor",  "item_calculo": "D-II-a",        "quantidade": 1},
        {"item_guia": "Contador",      "item_calculo": "E-I",           "quantidade": 1},
        {"item_guia": "Ofícios",       "item_calculo": "G-XX-a parte 2","usa_ids_oficios": True, "quantidade": 1},
        {"item_guia": "Custas",        "item_calculo": "G-I",           "usa_valor_causa_atualizado": True, "quantidade": 1},
    ],
    "familia": [],      # preencher conforme mapeamento da operadora
    "fazenda_publica": [],
    "criminal": [],     # inclui seção Multa Criminal
    "default": []       # → status pendente_manual + alerta no dashboard
}

def detectar_area(classe: str, feito: str) -> str:
    c = classe.lower()
    if any(x in c for x in ["família", "divórcio", "alimentos", "inventário", "partilha"]):
        return "familia"
    if any(x in c for x in ["fazenda", "tributário", "execução fiscal"]):
        return "fazenda_publica"
    if any(x in c for x in ["criminal", "penal", "crime", "contravenção"]):
        return "criminal"
    if any(x in c for x in ["procedimento comum", "indenização", "cobrança", "execução"]):
        return "civel_comum"
    return "default"
```

### 6.6 sistjweb.py — Preenchimento

#### Passo 1: Dados do Processo

```
1. Radio "Processo Eletrônico = Sim"
2. Radio instância (1ª ou 2ª)
3. Campo Número → numero_sem_mascara
4. Clicar Consultar
5. Aguardar preenchimento automático (Circunscrição, Competência, Feito, Classe)
6. LER "Valor da Causa Atualizado" da tela → salvar no banco
7. Preencher Valor da Causa (formato: 1.000,00)
8. Preencher Data de Distribuição (DD/MM/AAAA)
9. Preencher Polo Ativo
10. Preencher Polo Passivo (vazio → "Não Há")
```

#### Passo 2: Seção Custas

```
1. Tipo da Guia:
   - 1ª instância → "Guia Final - 1ª Instância"
   - 2ª instância → "Guia Final - 2ª Instância"
2. Pró-rata: marcar se múltiplos sucumbentes
3. Para cada sucumbente:
   - Se é o autor → clicar "Adicionar autor(es)"
   - Se não → preencher Nome, CPF/CNPJ, Tipo de parte, % ou Fração
   - Isenção de Custas → marcar se suspensao_exigibilidade = True
   - Clicar Adicionar
```

#### Passo 3: Peças Processuais

```
Preencher campo "Número das Folhas" de cada linha com os IDs correspondentes.
Formato: IDs separados por vírgula sem espaço.
Deixar vazio se não houver documentos do tipo.

Linhas:
- Ofícios           → ids_oficios
- Alvarás           → ids_alvaras
- Traslados         → ids_traslados
- Mandados          → ids_mandados
- Cartas de Sentença → ids_cartas_sentenca
- AR                → ids_ar
- AR/MP             → ids_armp
- Circunscrição de Origem → ids_circunscricao_origem
- Outra Circunscrição → ids_outra_circunscricao
```

#### Passo 4: Outros Itens (loop)

```
Para cada item em REGRAS_OUTROS_ITENS[area_direito]:
  1. Selecionar dropdown "Item da Guia"
  2. Aguardar radio buttons "Item de Cálculo" aparecerem
  3. Selecionar radio do item_calculo correspondente
  4. Se usa_valor_causa_atualizado: preencher campo Valor
  5. Se usa_ids_oficios: preencher Número das Folhas com IDs
  6. Preencher Quantidade se necessário
  7. Clicar Adicionar
  8. Verificar se apareceu na tabela
```

#### Passo 5: Custas Pagas

```
Para cada entrada em custas_pagas:
  1. Data do Pagamento (DD/MM/AAAA)
  2. Valor das Custas Pagas (sem R$, formato: 000.00)
  3. Número da Guia
  4. Clicar Adicionar
```

#### Passo 6: Salvar

```
1. Clicar Avançar → tela de resultado
2. Capturar "Valor Total a Recolher"
3. Tirar screenshot da tela
4. Clicar Gravar (NÃO "Gravar e Aprovar")
5. status → 'aguardando_aprovacao'
```

### 6.7 emissor.py — Após aprovação humana

```
1. Receber processo_id aprovado
2. Reconectar ao SISTJWEB se necessário
3. Navegar até o processo salvo
4. Clicar "Gravar e Aprovar"
5. Fazer download do Demonstrativo PDF
6. Salvar em /dados/demonstrativos/{numero}.pdf
7. pje.anexar(numero, caminho_pdf)
8. status → 'emitido'
```

---

## 7. API FASTAPI — Endpoints

```
GET  /processos              → lista aguardando_aprovacao + pendente_manual
GET  /processos/{id}         → detalhe completo
POST /aprovar/{id}           → dispara emissor
POST /rejeitar/{id}          → salva obs + status rejeitado
GET  /historico              → emitidos e rejeitados paginado
GET  /health                 → status do sistema
```

Autenticação: JWT simples ou HTTP Basic Auth via .env.

---

## 8. DASHBOARD — React + shadcn/ui

### /fila

```
- Cards de processos aguardando aprovação
- Badge de alerta para pendente_manual
- Cada card: número, polo ativo, polo passivo, valor total a recolher
- Botão Revisar → /detalhe/:id
```

### /detalhe/:id

```
Layout duas colunas:

Esquerda — dados extraídos (somente leitura):
  - Cabeçalho: número, instância, circunscrição, competência, feito, classe
  - Valores: causa, causa atualizado, data distribuição
  - Partes: polo ativo, polo passivo
  - Custas: tipo guia, pró-rata
  - Tabela sucumbentes: % | Nome | CPF/CNPJ | Tipo | Isenção
  - Tabela peças: Tipo | IDs inseridos
  - Tabela outros itens: Item Guia | Item Cálculo | Valor/Folhas | Qtd
  - Tabela custas pagas: Data | Valor | Nº Guia | Valor Atualizado
  - Destaque: Valor Total a Recolher

Direita — ações:
  - Screenshot do SISTJWEB preenchido
  - Textarea observações (obs_operador)
  - Botão Aprovar (verde)
  - Botão Rejeitar (vermelho)

Alertas no topo (shadcn Alert):
  ⚠️ "Área não mapeada — verifique Outros Itens manualmente"
  ⚠️ "Suspensão de exigibilidade detectada — confirmar isenção"
  ⚠️ "Sucumbente não identificado na sentença"
```

### /historico

```
- Tabela paginada: Número | Polo Ativo | Valor | Status | Data | Obs
- Filtros: status, data, circunscrição
```

### Componentes shadcn/ui

```
Card, Table, Badge, Button, Alert, Textarea,
Separator, Skeleton, Toast, Dialog
```

---

## 9. REGRAS DE NEGÓCIO

| Regra | Comportamento |
|---|---|
| Nunca reprocessar | Só processa status NULL ou 'erro' |
| Área não mapeada | status 'pendente_manual' + alerta no dashboard |
| Sucumbente = autor | Usar botão "Adicionar autor(es)" |
| Sucumbente = réu | Preencher manualmente |
| Sucumbente não identificado | Alerta no dashboard |
| Pró-rata | Marcar quando múltiplos sucumbentes |
| Isenção de custas | Marcar quando suspensao_exigibilidade = True |
| Valor causa atualizado | Ler da tela SISTJWEB após Consultar — nunca do PDF |
| Timeout sessão SISTJWEB | ~30 min — monitorar e reconectar |
| Máximo de tentativas | 3 por processo — depois: status 'erro' + email |
| Nunca parar o pipeline | Erro em um processo não para os demais |
| Gravar vs Gravar e Aprovar | Agente só clica "Gravar". "Gravar e Aprovar" só após aprovação humana |

---

## 10. ORDEM DE IMPLEMENTAÇÃO

1. Schema SQLite + db.py
2. config.py
3. datajud.py (testar com número real)
4. pje.py — login + lista (testar isolado)
5. parser.py — IDs + regex (testar com docs reais)
6. regras.py
7. sistjweb.py (testar em modo headful primeiro)
8. emissor.py
9. main.py — orquestrador
10. API FastAPI
11. Dashboard React
12. Docker Compose
13. Nginx + SSL + deploy VPS

---

## 11. NOTAS FINAIS

- Playwright em **headless** no VPS. Durante dev: `headless=False`.
- Screenshots salvas em `/dados/screenshots/{numero}/` para auditoria.
- **Nunca commitar .env**.
- O campo "Número das Folhas" no SISTJWEB recebe **IDs do PJE** — o label é enganoso.
- "Outros Itens" exige 4-5 interações Playwright por item: dropdown → radio → campo → Adicionar.
- "Valor da Causa Atualizado" é lido da tela após Consultar — não extraído de PDF.
- Logs em JSON estruturado.
