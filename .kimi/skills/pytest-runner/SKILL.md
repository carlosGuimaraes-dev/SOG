---
name: pytest-runner
description: >
  Use para executar e analisar testes com pytest.
  Inclui comandos de execução, filtros com -k, marcações com -m,
  cobertura, relatório de falhas, debug com --pdb e paralelização com pytest-xdist.
---

# pytest-runner

Execução e análise de testes pytest.

## Quando usar

- Durante desenvolvimento para validar mudanças.
- Em pipelines CI para garantir qualidade.
- Para investigar falhas intermitentes ou debugar testes quebrados.
- Para medir cobertura de código antes de merge.

## Padrões principais

### Comandos de execução

```bash
# Executar todos os testes
pytest

# Executar arquivo específico
pytest tests/test_login.py

# Executar função específica
pytest tests/test_login.py::test_login_success
```

### Filtros com -k

```bash
# Testes que contêm "login" no nome
pytest -k login

# Testes com "login" mas não "error"
pytest -k "login and not error"

# Testes com "user" ou "admin"
pytest -k "user or admin"
```

### Marcações com -m

```python
import pytest

@pytest.mark.slow
def test_processamento_longo():
    ...

@pytest.mark.integration
def test_database_connection():
    ...
```

```bash
# Executar apenas testes lentos
pytest -m slow

# Executar tudo exceto integração
pytest -m "not integration"

# Listar todas as marcações disponíveis
pytest --markers
```

### Cobertura

```bash
# Instalar plugin de cobertura
pip install pytest-cov

# Cobertura geral
pytest --cov=src

# Cobertura com relatório detalhado
pytest --cov=src --cov-report=term-missing

# Cobertura HTML
pytest --cov=src --cov-report=html

# Falhar se cobertura abaixo de 80%
pytest --cov=src --cov-fail-under=80
```

### Relatório de falhas

```bash
# Mostrar traceback completo
pytest -v

# Mostrar traceback longo
pytest -vv

# Parar no primeiro erro
pytest -x

# Mostrar saída de print mesmo em sucesso
pytest -s

# Relatório resumido com falhas no final
pytest -v --tb=short --lf
```

### Debug com --pdb

```bash
# Abrir PDB no primeiro erro
pytest --pdb

# Abrir PDB em cada falha
pytest --pdb -x

# Executar com ipdb (mais amigável)
pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Paralelização com pytest-xdist

```bash
# Instalar
pip install pytest-xdist

# Executar em paralelo usando todos os cores
pytest -n auto

# Executar em 4 processos
pytest -n 4

# Executar em paralelo por arquivo (evita conflito de estado)
pytest -n auto --dist=loadfile
```

## Anti-patterns

- `pytest -n auto` em testes com estado compartilhado (banco SQLite em arquivo) → falhas intermitentes.
- Usar `--pdb` em CI → build trava esperando input.
- Rodar suite completa sempre em vez de `-k` durante desenvolvimento → feedback lento.
- Ignorar `pytest.warns()` para warnings importantes.
