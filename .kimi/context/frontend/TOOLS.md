# TOOLS — Frontend Engineer

## `Think`
Use antes de implementar. Raciocine sobre:
- Qual o componente mais simples que resolve o problema?
- Há componentes existentes que podem ser reutilizados ou estendidos?
- Quais estados de UI são necessários?
- Há impacto em componentes compartilhados?
- A mudança é reversível? (guardrail Karpathy #3)

---

## `ReadFile`
Leia sempre antes de modificar:
- O componente que será alterado
- Componentes pai e filho relacionados
- Arquivos de estilo globais e tokens do design system
- Testes existentes do componente

---

## `Glob`
Use para mapear a estrutura de UI antes de planejar:
```
src/components/**/*.tsx    → todos os componentes
src/**/*.css               → todos os arquivos de estilo
src/**/*.stories.*         → Storybook stories
**/*.test.tsx              → testes de componente
```

---

## `Grep`
Use para entender o impacto de mudanças em componentes compartilhados:
```
"import Button"            → quem usa o componente Button?
"className=\"header\""     → onde a classe header é aplicada?
"data-testid"              → identificadores usados em testes E2E
```

---

## `Shell`
Use para:
- Instalar dependências de frontend (`npm install`, `pnpm add`)
- Rodar testes de componente (`npm test`, `vitest run`)
- Verificar linting e formatação (`eslint`, `prettier --check`)
- Rodar build para verificar erros de compilação (`npm run build`)

**Sempre verifique warnings de build — podem ser erros em produção.**

---

## `WriteFile`
Use para criar novos componentes, páginas ou arquivos de estilo.
Escreva sempre o arquivo completo.

---

## `StrReplaceFile`
Use para editar componentes existentes de forma cirúrgica.
Preferível a reescrever o arquivo inteiro.

---

## `SearchWeb` / `FetchURL`
Use para consultar:
- Documentação de libs de UI (shadcn, MUI, Radix, etc.)
- Referência de APIs do framework (React, Vue, etc.)
- Padrões WCAG e ARIA para acessibilidade
- Core Web Vitals e técnicas de otimização
