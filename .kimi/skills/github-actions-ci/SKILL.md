---
name: github-actions-ci
description: >
  Use para criar pipelines CI/CD com GitHub Actions.
  Inclui workflow syntax, jobs paralelos, cache, matrix strategy,
  secrets, artifacts, reusable workflows, pin por hash SHA e deploy com aprovação manual.
---

# github-actions-ci

Pipelines CI/CD com GitHub Actions.

## Quando usar

- Automatizar testes, build e deploy a cada push ou PR.
- Reutilizar workflows entre repositórios.
- Garantir consistência com cache e matrix de ambientes.

## Padrões principais

### Workflow syntax

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest
```

### Jobs paralelos

```yaml
jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Cache de dependências

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.11"
  - uses: actions/cache@v4
    with:
      path: ~/.cache/pip
      key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
  - run: pip install -r requirements.txt
```

### Matrix strategy

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
    os: [ubuntu-latest, macos-latest]

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Secrets e variáveis

```yaml
env:
  APP_ENV: ${{ vars.APP_ENV }}

steps:
  - run: docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASS }}
```

### Artifacts

```yaml
steps:
  - run: pytest --cov=src --cov-report=xml
  - uses: actions/upload-artifact@v4
    with:
      name: coverage-report
      path: coverage.xml
```

### Reusable workflows

```yaml
# .github/workflows/reusable-test.yml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
      - run: pytest
```

```yaml
# .github/workflows/ci.yml
jobs:
  call-test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: "3.11"
```

### Pin de actions por hash SHA

```yaml
steps:
  - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

### Deploy com aprovação manual

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    needs: [test, build]
    steps:
      - run: ./scripts/deploy.sh
```

Configure `environment: production` com **required reviewers** nas Settings do repositório.

## Anti-patterns

- Usar `@latest` ou `@v1` sem pin de SHA → builds não reprodutíveis.
- Secrets em `env` de steps sem necessidade → exposição acidental em logs.
- Cache sem `hashFiles` → cache stale entre builds.
- `needs` circular ou faltando → pipeline quebra ou roda fora de ordem.
