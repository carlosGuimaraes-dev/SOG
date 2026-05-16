---
name: react-vite-frontend
description: Desenvolvimento de aplicações React 18 com Vite. Use quando criar, estruturar ou refatorar o frontend React do projeto, configurar builds, hooks, estado, lazy loading ou integração com APIs REST.
---

# React 18 + Vite

## Resumo

Stack moderna para SPAs e dashboards: React 18 (Concurrent Features), Vite (dev server e build rápido), TypeScript e ES Modules. Foco em componentes funcionais, hooks nativos e integração REST.

## Quando usar

- Criar páginas, componentes reutilizáveis ou hooks no frontend.
- Configurar build, aliases, variáveis de ambiente ou code splitting.
- Integrar com APIs REST (fetch/axios).
- Migrar de CRA para Vite ou atualizar para React 18.

## Padrões principais

### Estrutura de projeto

```
src/
  components/       # Componentes reutilizáveis (Button, Card, Modal)
  pages/            # Rotas/páginas (Home, Dashboard)
  hooks/            # Hooks customizados
  contexts/         # Providers React Context
  services/         # Funções de API (fetch/axios)
  types/            # Tipos TypeScript globais
  utils/            # Helpers puros
```

### Hooks customizados

Prefixe com `use`. Encapsule lógica reutilizável e cleanup.

```ts
import { useState, useEffect } from 'react';

export function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(url)
      .then((r) => r.json())
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e); });
    return () => { cancelled = true; };
  }, [url]);

  return { data, error };
}
```

### Gerenciamento de estado

- **useState**: estado local simples.
- **useReducer**: estado complexo ou múltiplas ações.
- **Context**: estado global leve (temas, autenticação).

```ts
// useReducer para formulário
interface State { values: Record<string, string>; errors: Record<string, string>; }
type Action =
  | { type: 'SET_FIELD'; field: string; value: string }
  | { type: 'SET_ERROR'; field: string; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, values: { ...state.values, [action.field]: action.value } };
    case 'SET_ERROR':
      return { ...state, errors: { ...state.errors, [action.field]: action.error } };
    default:
      return state;
  }
}
```

### Integração com APIs REST

Use `fetch` nativo ou axios. Sempre trate erros e use `AbortController`.

```ts
// services/api.ts
const API_BASE = import.meta.env.VITE_API_URL;

export async function getProcessos() {
  const res = await fetch(`${API_BASE}/processos`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

### Lazy loading e code splitting

Use `React.lazy` + `Suspense` para rotas ou componentes pesados.

```tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <Suspense fallback={<div>Carregando...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

### Configuração do Vite (`vite.config.ts`)

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### Variáveis de ambiente

Prefixe com `VITE_` para expor ao cliente. Acesse via `import.meta.env`.

```
# .env
VITE_API_URL=http://localhost:8000
```

```ts
const apiUrl = import.meta.env.VITE_API_URL;
```

## Exemplos

### Componente funcional com props tipadas

```tsx
interface CardProps {
  title: string;
  children: React.ReactNode;
  onClick?: () => void;
}

export function Card({ title, children, onClick }: CardProps) {
  return (
    <div onClick={onClick} className="card">
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  );
}
```

### Context + Provider

```tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface AuthContextType {
  user: string | null;
  login: (u: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<string | null>(null);
  return (
    <AuthContext.Provider value={{ user, login: setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
```

## Anti-patterns

- **useEffect sem array de dependências** → causa reexecuções infinitas.
- **useState com objetos aninhados mutados** → sempre espalhe (`...`) ou use `useReducer`.
- **Context para estado de alta frequência** → use bibliotecas externas (Zustand, Jotai) ou levante o estado.
- **React.FC** → prefira tipar props diretamente na função.
- **Importar tudo de uma vez** → use `React.lazy` para rotas grandes.
- **`process.env` no Vite** → use `import.meta.env.VITE_*`.
