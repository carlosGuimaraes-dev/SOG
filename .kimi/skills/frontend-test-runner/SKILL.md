---
name: frontend-test-runner
description: >
  Use para executar testes frontend com Vitest.
  Inclui vitest run, modo watch, filtro de testes,
  relatórios, debug e integração CI.
---

# frontend-test-runner

Execução de testes frontend com Vitest.

## Quando usar

- Validar componentes React/Vue e lógica de estado.
- Executar suite antes de commits ou em CI.
- Debugar testes que falham apenas em ambiente específico.

## Padrões principais

### vitest run

```bash
# Executar todos os testes uma vez (CI)
npx vitest run

# Executar com cobertura
npx vitest run --coverage

# Executar em modo silencioso
npx vitest run --reporter=dot
```

### Modo watch

```bash
# Iniciar watch mode (desenvolvimento)
npx vitest

# Watch filtrando por arquivo
npx vitest src/components/Button.test.tsx
```

### Filtro de testes

```bash
# Filtrar por nome de teste
npx vitest -t "deve renderizar botão"

# Filtrar por padrão de arquivo
npx vitest src/components/

# Executar apenas testes que falharam na última execução
npx vitest --rerun-failed
```

### Relatórios

```bash
# Relatório JSON para CI
npx vitest run --reporter=json --outputFile=results.json

# Relatório HTML
npx vitest run --reporter=html

# Múltiplos reporters
npx vitest run --reporter=dot --reporter=junit --outputFile.junit=junit.xml
```

### Debug

```bash
# Executar com Node inspector
node --inspect-brk ./node_modules/vitest/vitest.mjs --run

# Mostrar logs de console dos testes
npx vitest run --reporter=verbose

# Isolar um teste com .only
import { test } from 'vitest'
test.only('isolar este', () => { ... })
```

### Integração CI

```yaml
# .github/workflows/ci.yml
jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npx vitest run --coverage --reporter=junit --outputFile.junit=junit.xml
      - uses: actions/upload-artifact@v4
        with:
          name: frontend-test-results
          path: junit.xml
```

```json
// package.json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Anti-patterns

- `test.only` commitado na main → testes ignorados silenciosamente.
- `vitest --watch` em CI → build nunca termina.
- Testes dependentes de ordem de execução (`test 1` cria dado para `test 2`).
- Não mockar chamadas de API → testes lentos e flaky.
