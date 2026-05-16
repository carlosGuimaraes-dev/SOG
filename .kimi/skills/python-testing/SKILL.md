---
name: python-testing
description: Testes Python com pytest. Estrutura de testes, fixtures, parametrização, mocks com unittest.mock, testes async, cobertura com pytest-cov e padrões de organização.
---

# Python Testing

## Resumo

Práticas de teste com pytest para garantir qualidade e manutenibilidade de código Python.

## Quando usar

- Toda vez que escrever código Python não trivial
- Antes de refatorar para garantir que não há regressões
- Para documentar comportamento esperado de funções
- Para testar integração entre componentes

## Padrões principais

### 1. Estrutura de testes

```
projeto/
├── src/
│   └── minha_lib.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_minha_lib.py
│   └── integration/
│       └── test_api.py
```

### 2. Fixtures

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def db_conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "test.db")
    yield conn
    conn.close()

@pytest.fixture
def mock_service():
    return MagicMock()
```

### 3. Parametrização

```python
import pytest

@pytest.mark.parametrize("entrada,esperado", [
    ("0809979-48.2024.8.07.0001", True),
    ("123", False),
    ("", False),
])
def test_validar_numero_processo(entrada, esperado):
    assert validar_numero(entrada) is esperado
```

### 4. Mocks com unittest.mock

```python
from unittest.mock import patch, MagicMock

def test_buscar_processo_externo():
    with patch("src.client.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"numero": "123"}
        resultado = buscar_processo("123")
        assert resultado["numero"] == "123"
        mock_get.assert_called_once()
```

### 5. Testes async

```python
import pytest

@pytest.mark.asyncio
async def test_login_pagina():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://pje.tjdft.jus.br/")
        assert await page.title() == "PJe"
        await browser.close()
```

### 6. Cobertura com pytest-cov

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

```ini
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

### 7. Padrões de organização

```python
# Given / When / Then
def test_calcula_custas():
    # Given
    processo = Processo(valor=1000.00)
    
    # When
    custas = processo.calcula_custas()
    
    # Then
    assert custas == 105.00
```

## Anti-patterns

- Testar dependências externas reais em vez de mocks
- Nomear testes genericamente (`test_1`, `test_func`)
- Não isolar estado entre testes (compartilhar DB mutável)
- Usar `sleep()` em testes async em vez de `asyncio.wait_for`
- Ignorar warnings do pytest
- Cobertura 100% como meta em vez de qualidade de testes
