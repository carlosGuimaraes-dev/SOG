---
name: sqlite-patterns
description: Padrões SQLite para aplicações Python. Conexão com context manager, migrations com versionamento, queries parametrizadas, índices para performance, WAL mode para concorrência, backup/restore e transações explícitas.
---

# SQLite Patterns

## Resumo

Uso robusto de SQLite em aplicações Python com foco em segurança, performance e integridade de dados.

## Quando usar

- Aplicações single-node ou containerizadas
- Cache local ou filas de trabalho
- Protótipos que podem escalar para PostgreSQL depois
- Quando a simplicidade de um arquivo único é preferível

## Padrões principais

### 1. Conexão com context manager

```python
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("/dados/db.sqlite")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
```

### 2. Queries parametrizadas

```python
# Correto
with get_db() as conn:
    conn.execute(
        "INSERT INTO processos (numero, valor) VALUES (?, ?)",
        (numero, valor),
    )

# Errado — NUNCA faça isso
conn.execute(f"INSERT INTO processos VALUES ('{numero}', {valor})")
```

### 3. Migrations com versionamento

```python
import hashlib

MIGRATIONS = {
    1: """
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            valor REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    2: """
        CREATE INDEX IF NOT EXISTS idx_processos_numero ON processos(numero);
    """,
}

def run_migrations():
    with get_db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current = row[0] or 0

        for version, sql in sorted(MIGRATIONS.items()):
            if version > current:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (version,),
                )
                conn.commit()
```

### 4. Índices para performance

```python
# Campos frequentemente buscados ou filtrados
CREATE INDEX idx_processos_numero ON processos(numero);
CREATE INDEX idx_custas_status ON custas(status, criado_em);
```

### 5. WAL mode para concorrência

```python
with get_db() as conn:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
```

### 6. Backup e restore

```python
import shutil
from datetime import datetime

def backup_db():
    backup_path = DB_PATH.with_suffix(f".backup_{datetime.now():%Y%m%d_%H%M%S}.sqlite")
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        shutil.copy2(DB_PATH, backup_path)
    return backup_path

def restore_db(backup_path: Path):
    shutil.copy2(backup_path, DB_PATH)
```

### 7. Transações explícitas

```python
with get_db() as conn:
    try:
        conn.execute("BEGIN")
        conn.execute("INSERT INTO processos ...", (numero,))
        conn.execute("INSERT INTO custas ...", (valor,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

## Anti-patterns

- Usar f-string ou concatenação em queries SQL
- Ignorar transações em operações multi-tabela
- Não usar WAL mode em aplicações com concorrência
- Omitir índices em colunas de busca frequente
- Guardar arquivos SQLite em volumes compartilhados por NFS
- Não versionar o schema (migrations)
