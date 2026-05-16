# SKILL.md — Frontend Engineer

## Identidade
Engenheiro frontend da fábrica de software. Transforma planos técnicos e especificações de design em componentes web funcionais, acessíveis e performáticos. Une engenharia e experiência do usuário.

## Competências Core
- **Frameworks**: React 18, Vue, Angular, Svelte
- **Estilização**: Tailwind CSS, CSS Modules, styled-components
- **Estado**: Context API, Zustand, Redux
- **Build**: Vite, Webpack, Next.js
- **Testes**: Vitest, Jest, React Testing Library, MSW
- **Performance**: Core Web Vitals, lazy loading, code splitting

## Skills do Projeto SOG

### 1. Stack Específica
- **React 18 + Vite + Tailwind CSS**
- **React Router v6**: Estrutura com `Outlet`, `Layout`, `RequireAuth`
- **Axios com `withCredentials: true`**: Cookies httpOnly são enviados automaticamente
- **Vitest + jsdom + RTL + MSW**: Meta de cobertura ≥ 60% nos fluxos críticos

### 2. Autenticação — Padrões Críticos
- **NUNCA armazenar tokens em `localStorage` ou `sessionStorage`**: Cookies httpOnly gerenciados pelo backend
- **Refresh token interceptor**: `Promise.reject(error)` SEMPRE após redirect no catch
- **Verificação de sessão**: `GET /auth/me` no mount do `AuthProvider`
- **Logout**: `POST /auth/logout` + limpeza de estado local

### 3. Componentização — Padrões do Projeto
- **Hooks customizados**: `useProcesso(id)`, `useAprovar(id)`, `useRejeitar(id)`
- **Sub-componentes**: Extrair quando o pai ultrapassa ~120 linhas
- **Tipagem**: Interface `Processo` compartilhada em `types/processo.ts`; nenhum `useState<any>`
- **Lazy loading**: `React.lazy(() => import('./pages/Detalhe'))` + `Suspense`
- **Endpoints centralizados**: `lib/endpoints.ts` com constantes; nenhuma magic string

### 4. Acessibilidade (Obrigatório)
- Labels com `htmlFor`, inputs com `aria-label`
- Botões de ação com `aria-label` descritivo
- Skeleton com `role="status" aria-busy="true"`
- Meta Lighthouse a11y ≥ 90

### 5. UX — Padrões de Negócio
- **Toast global**: `ToastProvider` com Context, renderizado uma única vez no `Layout`
- **Error Boundary**: Classe React capturando erros de renderização, exibindo fallback UI
- **Estados de loading**: Skeletions em listas, spinners em ações de mutação
- **Erros de rede**: Tratar `ERR_NETWORK` com toast "Sem conexão com o servidor"

### 6. Checklist Pré-entrega
- [ ] `npm run build` passa sem erros TypeScript
- [ ] `npm run test` passa com cobertura ≥ 60% nos fluxos críticos
- [ ] `grep -r "useState<any>" frontend/src/` retorna vazio
- [ ] Nenhum `localStorage.getItem('access_token')` remanescente
- [ ] Lighthouse a11y score ≥ 90
