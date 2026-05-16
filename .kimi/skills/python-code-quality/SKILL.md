---
name: python-code-quality
description: >
  Use para garantir qualidade de código Python.
  Inclui PEP 8, type hints, docstrings (Google/NumPy),
  complexidade ciclomática, linting com ruff/flake8,
  formatação com black e imports organizados.
---

# python-code-quality

Qualidade de código Python.

## Quando usar

- Antes de abrir PRs.
- Configurar hooks de pre-commit.
- Revisar código legado para modernização.
- Padronizar estilo em equipe.

## Padrões principais

### PEP 8

- 4 espaços para indentação.
- Linha máxima: 88 (Black) ou 79 (PEP 8 estrito).
- `snake_case` para funções/variáveis; `PascalCase` para classes.
- Uma importação por linha; agrupar: stdlib, third-party, local.

### Type hints

```python
from typing import Optional, List, Dict

def buscar_usuario(user_id: int) -> Optional[dict]:
    ...

def processar_itens(itens: List[str]) -> Dict[str, int]:
    ...
```

### Docstrings

**Google style:**

```python
def calcular_total(preco: float, quantidade: int) -> float:
    """Calcula o total de um item.

    Args:
        preco: Preço unitário do item.
        quantidade: Quantidade comprada.

    Returns:
        Valor total da compra.

    Raises:
        ValueError: Se preço ou quantidade forem negativos.
    """
    if preco < 0 or quantidade < 0:
        raise ValueError("Valores não podem ser negativos")
    return preco * quantidade
```

**NumPy style:**

```python
def calcular_total(preco: float, quantidade: int) -> float:
    """Calcula o total de um item.

    Parameters
    ----------
    preco : float
        Preço unitário do item.
    quantidade : int
        Quantidade comprada.

    Returns
    -------
    float
        Valor total da compra.
    """
    return preco * quantidade
```

### Complexidade ciclomática

```bash
# Instalar e verificar complexidade
pip install mccabe
python -m mccabe --min 10 src/
```

Mantenha funções com complexidade < 10. Extraia funções auxiliares quando necessário.

### Linting com ruff

```bash
# Instalar
pip install ruff

# Verificar
cd /Users/carlosguimaraes/Projects/SOG && ruff check .

# Verificar e tentar corrigir
ruff check . --fix

# Verificar organização de imports
ruff check . --select I
```

### Formatação com black

```bash
# Instalar
pip install black

# Formatar
cd /Users/carlosguimaraes/Projects/SOG && black .

# Verificar sem alterar
black --check .
```

### Imports organizados

```python
# stdlib
import os
from datetime import datetime

# third-party
import requests
from pydantic import BaseModel

# local
from src.config import settings
from src.models import User
```

Configure no `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "W"]

[tool.black]
line-length = 88
target-version = ["py311"]
```

## Anti-patterns

- `# noqa` genérico sem especificar regra → esconde problemas reais.
- Type hints opcionais em APIs públicas → dificulta uso e manutenção.
- Funções com 50+ linhas e múltiplos níveis de aninhamento.
- Imports circulares resolvidos com imports dentro de funções.
- Mixar `'` e `"` sem padrão → use um formatter.
