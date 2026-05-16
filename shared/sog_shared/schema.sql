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

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_jti TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
