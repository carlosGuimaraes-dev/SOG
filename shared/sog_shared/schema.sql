CREATE TABLE IF NOT EXISTS processos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    numero_sem_mascara TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente',
    -- status: pendente | aguardando_aprovacao | aprovado | rejeitado | emitido | erro | pendente_manual
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    tentativas INTEGER DEFAULT 0,
    erro_msg TEXT,
    reprocessar_solicitado_em DATETIME,
    reprocessar_solicitado_por TEXT,
    reprocessar_motivo TEXT
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

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_jti TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agente_controle (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- sempre exatamente 1 linha
    comando TEXT NOT NULL DEFAULT 'parar',    -- iniciar | parar
    status TEXT NOT NULL DEFAULT 'parado',    -- parado | iniciando | autenticando | executando | dormindo | aguardando_login | erro | parando | interrompido | pausado | erro_pausado
    mensagem TEXT DEFAULT '',
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    pid INTEGER,                              -- PID do processo agente no host
    ciclo_uuid TEXT,
    ciclo_snapshot TEXT DEFAULT '{}',
    pausado_em DATETIME,
    retomado_em DATETIME
);

CREATE TABLE IF NOT EXISTS agente_ciclos (
    uuid TEXT PRIMARY KEY,
    rotulo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'iniciando',
    -- status: iniciando | executando | aguardando_login | concluido | cancelado | erro
    iniciado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    fechado_em DATETIME,
    finalizado_em DATETIME,
    total_membros INTEGER NOT NULL DEFAULT 0,
    total_novos INTEGER NOT NULL DEFAULT 0,
    total_rearmados INTEGER NOT NULL DEFAULT 0,
    total_concluidos INTEGER NOT NULL DEFAULT 0,
    total_erros INTEGER NOT NULL DEFAULT 0,
    erro_msg TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agente_ciclo_membros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo_uuid TEXT NOT NULL REFERENCES agente_ciclos(uuid),
    processo_id INTEGER NOT NULL REFERENCES processos(id),
    numero TEXT NOT NULL,
    numero_sem_mascara TEXT NOT NULL,
    origem TEXT NOT NULL,
    -- origem: novo_pje | rearmado
    status_snapshot TEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ciclo_uuid, processo_id),
    UNIQUE(ciclo_uuid, numero)
);

CREATE TABLE IF NOT EXISTS agente_tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pendente',
    -- status: pendente | executando | concluido | erro | cancelado
    resultado TEXT DEFAULT '{}',
    mensagem_erro TEXT,
    sistema_alvo TEXT,
    -- sistema_alvo: pje | sistj | ambos
    criado_por TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    iniciado_em DATETIME,
    concluido_em DATETIME,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tarefas_status ON agente_tarefas(status, criado_em);
CREATE INDEX IF NOT EXISTS idx_tarefas_sistema ON agente_tarefas(sistema_alvo, status);
CREATE INDEX IF NOT EXISTS idx_ciclos_status ON agente_ciclos(status, criado_em);
CREATE INDEX IF NOT EXISTS idx_ciclo_membros_uuid ON agente_ciclo_membros(ciclo_uuid, id);
