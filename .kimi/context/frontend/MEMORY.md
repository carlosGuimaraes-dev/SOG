# MEMORY — Frontend Engineer

> Arquivo dinâmico. Registre padrões de UI, design system e gotchas do projeto.

---

## Stack de frontend

- **Framework:** React 18 + TypeScript
- **Router:** react-router-dom v6
- **Build:** Vite 5
- **HTTP Client:** Axios
- **Estilização:** Tailwind CSS v4
- **Testes:** Vitest + @testing-library/react + @testing-library/jest-dom + @testing-library/user-event + jsdom + MSW (instalado, mock via vi.mock no momento)
- **Lint:** ESLint (scripts configurados no package.json)

---

## Design system e tokens

- CSS custom properties em `index.css`
- Cores semânticas: `--background`, `--foreground`, `--primary`, `--destructive`, `--success`, `--warning`, `--muted`, `--card`, `--border`, `--input`, `--ring`
- Dark mode via classe `dark` no `<html>`

---

## Componentes reutilizáveis mapeados

| Componente | Path | Notas |
|---|---|---|
| Button | `src/components/ui/Button.tsx` | Variantes: default, outline, ghost, destructive. Tamanhos: default, sm, lg |
| Input | `src/components/ui/Input.tsx` | ForwardRef, aceita todas props de `<input>` |
| Textarea | `src/components/ui/Textarea.tsx` | ForwardRef, componente reutilizável (novo Wave 5) |
| Card | `src/components/ui/Card.tsx` | Card, CardHeader, CardTitle, CardContent |
| Alert | `src/components/ui/Alert.tsx` | Alert, AlertTitle, AlertDescription. Variante warning |
| Badge | `src/components/ui/Badge.tsx` | Variantes: default, success, destructive, warning |
| Skeleton | `src/components/ui/Skeleton.tsx` | Loading placeholder com `role="status" aria-busy="true"` |
| ThemeToggle | `src/components/ThemeToggle.tsx` | Extraído de App.tsx (Wave 5) |
| ErrorBoundary | `src/components/ErrorBoundary.tsx` | Classe React com fallback UI (Wave 5) |
| ToastProvider | `src/components/ToastProvider.tsx` | Context global para toasts (Wave 5) |

---

## Sub-componentes de Detalhe (Wave 5)

| Componente | Path | Responsabilidade |
|---|---|---|
| DadosProcessoCard | `src/components/detalhe/DadosProcessoCard.tsx` | Grid de dados do processo |
| SucumbentesTable | `src/components/detalhe/SucumbentesTable.tsx` | Tabela de sucumbentes |
| ScreenshotCard | `src/components/detalhe/ScreenshotCard.tsx` | Imagem do screenshot com fallback |
| AcoesPanel | `src/components/detalhe/AcoesPanel.tsx` | Textarea + botões aprovar/rejeitar |
| PecasProcessuaisCard | `src/components/detalhe/PecasProcessuaisCard.tsx` | Lista de IDs PJE |
| OutrosItensTable | `src/components/detalhe/OutrosItensTable.tsx` | Tabela de outros itens |
| CustasPagasTable | `src/components/detalhe/CustasPagasTable.tsx` | Tabela de custas pagas |
| AvisosAlert | `src/components/detalhe/AvisosAlert.tsx` | Alertas de validação |
| ValorTotal | `src/components/detalhe/ValorTotal.tsx` | Exibição do valor total |

---

## Hooks customizados (Wave 5)

| Hook | Path | Função |
|---|---|---|
| useProcesso | `src/hooks/useProcesso.ts` | Fetch dados do processo por ID |
| useAprovar | `src/hooks/useAprovar.ts` | Ação de aprovação + navegação |
| useRejeitar | `src/hooks/useRejeitar.ts` | Ação de rejeição + navegação |
| useToast | `src/hooks/useToast.ts` | Re-exporta do ToastProvider (compat) |

---

## Padrões de código de UI

- **Toast global:** `ToastProvider` em `src/components/ToastProvider.tsx` — renderizado uma única vez no `App.tsx`. Nunca replicar UI de toast em páginas.
- **API:** Instância axios centralizada em `src/lib/api.ts` com interceptors. Trata `ERR_NETWORK` via evento customizado `api:network-error`.
- **Auth:** Contexto `AuthProvider` em `src/lib/auth.tsx` — verifica sessão via `/auth/me`. Usa `ENDPOINTS` (Wave 5).
- **Tema:** Contexto `ThemeProvider` em `src/lib/theme.tsx` — persiste preferência em `localStorage` (chave `sog-theme`).
- **Endpoints:** Constantes centralizadas em `src/lib/endpoints.ts` (Wave 5). Nunca usar strings mágicas de API.
- **Tipos:** `src/types/processo.ts` com interfaces `Processo`, `ProcessoHistorico`, `ProcessoCompleto`, `DadosProcesso`, etc. (Wave 5).
- **Pages:** Fila, Detalhe, Historico, Login — todas em `src/pages/`. Detalhe e Historico são lazy-loaded (Wave 5).

---

## Gotchas de CSS / framework

- **React Router v6:** NÃO usar `<Routes>` aninhados. Use `<Outlet />` + rotas filhas.
- **Axios com cookies:** Todas as requisições usam `withCredentials: true` para cookies httpOnly.
- **Base URL da API:** `/api/v1`.
- **Lazy loading:** `React.lazy` + `Suspense` com `Skeleton` como fallback para Detalhe e Historico.
- **ErrorBoundary:** Envolve `<Routes>` no App.tsx. Qualquer erro de renderização mostra UI de fallback com botão "Recarregar página".

---

## Débitos de UI identificados

- Nenhum teste escrito para `Historico.tsx` (cobertura 0%, mas média global > 60%).
- `App.tsx` e `main.tsx` não cobertos por testes (cobertura 0% nesses arquivos).
- React Router v6 future flags warnings (não crítico, não quebra funcionalidade).

---

## Histórico de implementações

### Wave 3 — Auth Cross-Cutting (2026-05-15)
- **CR-006:** Removido JWT de localStorage. Auth usa cookies httpOnly (`withCredentials: true`).
- **CR-010:** Fixado erro silenciado no refresh — `return Promise.reject(error)` garantido.
- **CR-005 / HI-014:** Screenshot carregado via `/api/v1/processos/{id}/screenshot` com tratamento de erro 404.
- **CR-011:** Routing refatorado para react-router-dom v6 com `<Outlet />` — sem `<Routes>` aninhados.
- **F-001:** Login.tsx com labels `htmlFor`, inputs `aria-label`, campo senha com `type="password"`.

### Wave 5 — Frontend: Refatoração, UX e Testes (2026-05-15)
- **HI-008:** Criado `ErrorBoundary.tsx` (classe React) com fallback UI. Envolve `<Routes>` no App.tsx.
- **HI-003:** Configurado Vitest + Testing Library + jsdom. 12 testes passando (Login, Fila, Detalhe). Cobertura > 66% nos fluxos críticos.
- **HI-004 / M-026 / M-031:** Refatorado `Detalhe.tsx` de 338 para 98 linhas. Extraídos hooks (`useProcesso`, `useAprovar`, `useRejeitar`) e 9 sub-componentes. Tipagem `ProcessoCompleto` substituiu `useState<any>`.
- **M-025 / M-030:** Criado `ToastProvider` com React Context. `<ToastContainer />` renderizado uma única vez no App.tsx. Removida replicação de toasts de Fila, Detalhe, Historico.
- **M-027:** Criado `src/types/processo.ts` com interface `Processo` compartilhada. Eliminada duplicação entre Fila e Historico.
- **M-028:** Criado `src/lib/endpoints.ts` com constantes `ENDPOINTS`. Substituídas strings mágicas em todos os componentes.
- **M-029:** Adicionado `React.lazy` + `Suspense` para `Detalhe` e `Historico`. Build gera chunks separados.
- **M-032:** Adicionados `aria-label` em todos os botões de ação (Aprovar, Rejeitar, Voltar, Sair, Alternar tema, Revisar).
- **M-033:** Extraído `ThemeToggle` para `src/components/ThemeToggle.tsx`.
- **M-035:** `Skeleton.tsx` com `role="status" aria-busy="true" aria-label="Carregando..."`.
- **F-002:** `api.ts` trata `error.code === 'ERR_NETWORK'` emitindo evento customizado `api:network-error`, consumido pelo ToastProvider.
