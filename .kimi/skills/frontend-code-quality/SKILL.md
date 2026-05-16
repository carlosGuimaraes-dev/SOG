---
name: frontend-code-quality
description: >
  Use para garantir qualidade de código frontend.
  Inclui ESLint, Prettier, convenções de nomenclatura,
  organização de imports, evitar prop drilling,
  memoização quando necessário e tipagem TypeScript.
---

# frontend-code-quality

Qualidade de código frontend.

## Quando usar

- Antes de abrir PRs no frontend.
- Configurar hooks de pre-commit e CI.
- Revisar componentes React/Vue para manutenibilidade.
- Migrar JavaScript para TypeScript.

## Padrões principais

### ESLint

```bash
# Executar lint
npx eslint src/

# Corrigir automaticamente
npx eslint src/ --fix
```

```json
// .eslintrc.json
{
  "extends": ["eslint:recommended", "plugin:react/recommended", "plugin:@typescript-eslint/recommended"],
  "rules": {
    "no-console": "warn",
    "react/prop-types": "off"
  }
}
```

### Prettier

```bash
# Formatar
npx prettier --write "src/**/*.{ts,tsx,css}"

# Verificar
npx prettier --check "src/**/*.{ts,tsx,css}"
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2
}
```

### Convenções de nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Componente | PascalCase | `UserCard.tsx` |
| Hook | camelCase, prefixo `use` | `useAuth.ts` |
| Função utilitária | camelCase | `formatDate.ts` |
| Constante | SCREAMING_SNAKE_CASE | `MAX_RETRIES = 3` |
| Interface/Type | PascalCase, prefixo opcional | `UserProps`, `ApiResponse` |
| Arquivo de estilo | kebab-case | `user-card.module.css` |

### Organização de imports

```tsx
// 1. React / framework
import React, { useState } from 'react'

// 2. Bibliotecas externas
import axios from 'axios'

// 3. Componentes absolutos
import { Button } from '@/components/Button'

// 4. Hooks / utils
import { useAuth } from '@/hooks/useAuth'
import { formatDate } from '@/utils/formatDate'

// 5. Estilos
import styles from './UserCard.module.css'
```

### Evitar prop drilling

```tsx
// ❌ Prop drilling através de múltiplos níveis
<App user={user} />
  <Layout user={user} />
    <Header user={user} />
      <UserMenu user={user} />

// ✅ Context API ou state management
const UserContext = createContext(null)

function App() {
  return (
    <UserContext.Provider value={user}>
      <Layout />
    </UserContext.Provider>
  )
}

function UserMenu() {
  const user = useContext(UserContext)
  return <span>{user.name}</span>
}
```

### Memoização quando necessário

```tsx
import { memo, useMemo, useCallback } from 'react'

// Memoizar componente filho que recebe props pesadas
const ExpensiveList = memo(function ExpensiveList({ items }) {
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  )
})

function Parent() {
  const [count, setCount] = useState(0)
  const items = useMemo(() => gerarListaPesada(), [])
  const handleClick = useCallback(() => setCount(c => c + 1), [])

  return (
    <>
      <button onClick={handleClick}>Count: {count}</button>
      <ExpensiveList items={items} />
    </>
  )
}
```

### Tipagem TypeScript

```tsx
interface UserCardProps {
  name: string
  email: string
  avatarUrl?: string
  onClick: (id: string) => void
}

export function UserCard({ name, email, avatarUrl, onClick }: UserCardProps) {
  return (
    <div onClick={() => onClick(email)}>
      {avatarUrl && <img src={avatarUrl} alt={name} />}
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  )
}
```

## Anti-patterns

- `any` sem justificativa → perde proteção do TypeScript.
- `useMemo`/`useCallback` em tudo → overhead sem ganho real.
- `console.log` em produção → use `console.warn`/`error` ou remova.
- Componentes com 300+ linhas → extraia subcomponentes.
- Importar tudo de uma biblioteca (`import * as _ from 'lodash'`) → aumenta bundle.
