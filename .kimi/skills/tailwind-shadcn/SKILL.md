---
name: tailwind-shadcn
description: Estilização com Tailwind CSS e shadcn/ui. Use quando criar componentes, configurar temas, ajustar responsividade, implementar dark mode ou instalar/customizar componentes shadcn/ui no frontend.
---

# Tailwind CSS + shadcn/ui

## Resumo

Tailwind fornece utilitários CSS-atômicos; shadcn/ui fornece componentes acessíveis e customizáveis baseados em Radix + Tailwind. Juntos permitem UI rápida, consistente e sem dependência de pacote de componentes.

## Quando usar

- Criar ou estilizar componentes React.
- Configurar tema (cores, fontes, espaçamento).
- Implementar dark mode ou responsividade mobile-first.
- Instalar e customizar componentes shadcn/ui (Button, Dialog, Table, etc.).
- Criar variantes de componentes com `class-variance-authority`.

## Padrões principais

### Configuração do Tailwind (`tailwind.config.js`)

```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1e3a8a',
          foreground: '#ffffff',
        },
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

### CSS variables para tema

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
  }
}
```

### Uso de utilitários Tailwind

Prefira composição direta nas classes. Use `@apply` apenas quando necessário.

```tsx
<button
  className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
>
  Salvar
</button>
```

### Componentes shadcn/ui (instalação e customização)

```bash
npx shadcn add button dialog table
```

Os componentes são copiados para `src/components/ui/` e podem ser editados diretamente.

```tsx
// src/components/ui/button.tsx (exemplo adaptado)
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
```

### Dark mode

Use uma classe no `<html>` ou `<body>` e toggle via estado/contexto.

```tsx
// src/components/ThemeProvider.tsx
import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext({ theme: 'light', toggle: () => {} });

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggle: () => setTheme((t) => (t === 'light' ? 'dark' : 'light')) }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

### Responsividade mobile-first

```tsx
<div className="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 lg:grid-cols-3">
  <Card />
  <Card />
  <Card />
</div>
```

### Variantes com `class-variance-authority`

Use `cva` para criar variantes de estilo tipadas e combináveis.

```ts
import { cva } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);
```

## Exemplos

### Card com shadcn/ui + Tailwind

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export function ProcessoCard({ numero, status }: { numero: string; status: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{numero}</CardTitle>
      </CardHeader>
      <CardContent>
        <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
          {status}
        </span>
      </CardContent>
    </Card>
  );
}
```

## Anti-patterns

- **Classes arbitrárias para tudo** → use `@layer components` ou `cva` para padrões repetidos.
- **`!important` excessivo** → Tailwind já tem `!`, mas abuse indica má arquitetura.
- **Dark mode via `dark:` em cada elemento** → use CSS variables e troca de classe no root.
- **Instalar shadcn/ui e nunca customizar** → os componentes são seus; ajuste conforme o design.
- **`class-variance-authority` com lógica de negócio** → mantenha `cva` apenas para estilo.
