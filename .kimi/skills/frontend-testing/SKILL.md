---
name: frontend-testing
description: Testes de frontend com Vitest e React Testing Library. Use quando escrever, executar ou depurar testes de componentes, hooks, interações de usuário ou cobertura de código no frontend React.
---

# Testes de Frontend (Vitest + React Testing Library)

## Resumo

Vitest substitui o Jest com API compatível e execução mais rápida. React Testing Library testa componentes como o usuário os vê, priorizando queries acessíveis e eventos realistas.

## Quando usar

- Escrever testes para componentes React, hooks ou utilitários.
- Configurar cobertura de código (`v8` ou `istanbul`).
- Mockar módulos, APIs ou timers.
- Testar interações assíncronas (fetch, loaders, animações).
- Executar testes em CI ou localmente.

## Padrões principais

### Configuração do Vitest (`vitest.config.ts`)

```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
});
```

### Setup com Testing Library

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
```

### Testes de componentes

Prefira `screen` e queries acessíveis (`getByRole`, `getByLabelText`).

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renderiza com texto', () => {
    render(<Button>Salvar</Button>);
    expect(screen.getByRole('button', { name: /salvar/i })).toBeInTheDocument();
  });

  it('dispara onClick', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Clique</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### `userEvent` vs `fireEvent`

Use `userEvent` para interações realistas (digitação, tab, hover).

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from './Input';

it('digita no campo', async () => {
  render(<Input label="Nome" />);
  const input = screen.getByLabelText(/nome/i);
  await userEvent.type(input, 'Maria');
  expect(input).toHaveValue('Maria');
});
```

### Mocks de módulos

```ts
import { vi } from 'vitest';

vi.mock('@/services/api', () => ({
  getProcessos: vi.fn().mockResolvedValue([{ id: 1, numero: '0001' }]),
}));
```

Mock de `fetch`:

```ts
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: [] }),
  } as Response)
);
```

### Testes assíncronos (`waitFor`)

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ProcessoList } from './ProcessoList';

it('exibe lista após carregar', async () => {
  render(<ProcessoList />);
  expect(screen.getByText(/carregando/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByText('0001')).toBeInTheDocument();
  });
});
```

### Cobertura de código

```bash
npx vitest --coverage
```

Configure no `vitest.config.ts` e ignore arquivos de configuração/teste.

### Testes de hooks com `renderHook`

```tsx
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

it('incrementa contador', () => {
  const { result } = renderHook(() => useCounter());
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

## Exemplos

### Teste de formulário completo

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormProcesso } from './FormProcesso';
import { vi } from 'vitest';

it('envia formulário com dados válidos', async () => {
  const onSubmit = vi.fn();
  render(<FormProcesso onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText(/número/i), '12345');
  await userEvent.click(screen.getByRole('button', { name: /enviar/i }));

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ numero: '12345' }));
  });
});
```

## Anti-patterns

- **Testar implementação, não comportamento** → não verifique `state` interno; verifique o DOM.
- **`getByText` para tudo** → prefira `getByRole`, `getByLabelText`.
- **Esquecer `await` em `userEvent`** → `userEvent` retorna Promise.
- **Não limpar mocks entre testes** → use `vi.clearAllMocks()` ou `beforeEach`.
- **Testes grandes e acoplados** → cada teste deve validar uma coisa.
