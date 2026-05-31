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
| AgenteStatusBar | `src/components/agente/AgenteStatusBar.tsx` | Barra de status do agente com bolinha, mensagem, botões Iniciar/Parar e polling a cada 5s (Fase 1.2) |

---

## Sub-componentes de Detalhe (Wave 5 + Wave 1)

| Componente | Path | Responsabilidade |
|---|---|---|
| DadosProcessoCard | `src/components/detalhe/DadosProcessoCard.tsx` | Grid de dados do processo |
| SucumbentesTable | `src/components/detalhe/SucumbentesTable.tsx` | Tabela de sucumbentes |
| ScreenshotCard | `src/components/detalhe/ScreenshotCard.tsx` | Imagem do screenshot com fallback |
| AcoesPanel | `src/components/detalhe/AcoesPanel.tsx` | Textarea + botões aprovar/rejeitar |
| DocumentosPje | `src/components/detalhe/DocumentosPje.tsx` | Tabela de documentos PJE (tipo, data assinatura, nome) — Wave 2 |
| CompensacaoTable | `src/components/detalhe/CompensacaoTable.tsx` | Tabela de compensação (data, valor, guia origem) — Wave 2 |
| EmissaoStatus | `src/components/detalhe/EmissaoStatus.tsx` | Spinner + polling de status pós-aprovação — Wave 2 |
| PecasProcessuaisCard | `src/components/detalhe/PecasProcessuaisCard.tsx` | Lista de IDs PJE |
| OutrosItensTable | `src/components/detalhe/OutrosItensTable.tsx` | Tabela de outros itens |
| CustasPagasTable | `src/components/detalhe/CustasPagasTable.tsx` | Tabela de custas pagas |
| AvisosAlert | `src/components/detalhe/AvisosAlert.tsx` | Alertas de validação |
| ValorTotal | `src/components/detalhe/ValorTotal.tsx` | Exibição do valor total |
| LogsTimeline | `src/components/detalhe/LogsTimeline.tsx` | Timeline vertical de logs com status colorido (ok/erro/aviso) |
| ErroBanner | `src/components/detalhe/ErroBanner.tsx` | Alerta de erro na execução (variant destructive) |
| ResumoPreenchimento | `src/components/detalhe/ResumoPreenchimento.tsx` | Card compacto com sucumbente, peças, itens e valor total |
| LinkPje | `src/components/detalhe/LinkPje.tsx` | Link externo para consulta do processo no PJE |
| BuscaProcesso | `src/components/fila/BuscaProcesso.tsx` | Input de busca com ícone e botão limpar |
| DemonstrativoLink | `src/components/detalhe/DemonstrativoLink.tsx` | Link para PDF do demonstrativo com verificação HEAD — Wave 3 |
| PrioridadeBadge | `src/components/fila/PrioridadeBadge.tsx` | Badge de prioridade (urgente/alto valor/antigo) — Wave 3 |
| Paginacao | `src/components/historico/Paginacao.tsx` | Controles de paginação client-side — Wave 3 |
| FiltrosHistorico | `src/components/historico/FiltrosHistorico.tsx` | Painel de filtros por status, data e valor mínimo — Wave 3 |
| BotaoExportar | `src/components/historico/BotaoExportar.tsx` | Botão de download CSV via `api.get(blob)` — Wave 3 |

---

## Hooks customizados (Wave 5)

| Hook | Path | Função |
|---|---|---|
| useProcesso | `src/hooks/useProcesso.ts` | Fetch dados do processo por ID |
| useAprovar | `src/hooks/useAprovar.ts` | Ação de aprovação + navegação |
| useRejeitar | `src/hooks/useRejeitar.ts` | Ação de rejeição + navegação |
| useToast | `src/hooks/useToast.ts` | Re-exporta do ToastProvider (compat) |
| usePollingStatus | `src/hooks/usePollingStatus.ts` | Polling de status do processo a cada N ms (default 5s). Para quando status ≠ 'aprovado'. Cleanup no unmount — Wave 2 |

---

## Libs utilitárias

| Lib | Path | Função |
|---|---|---|
| formatters.ts | `src/lib/formatters.ts` | `parseValorMonetario()` — remove `R$`, pontos de milhar, troca vírgula por ponto. Retorna `0` para input vazio/inválido — Wave 2 |

---

## Padrões de código de UI

- **Toast global:** `ToastProvider` em `src/components/ToastProvider.tsx` — renderizado uma única vez no `App.tsx`. Nunca replicar UI de toast em páginas.
- **API:** Instância axios centralizada em `src/lib/api.ts` com interceptors. Trata `ERR_NETWORK` via evento customizado `api:network-error`.
- **Auth:** Contexto `AuthProvider` em `src/lib/auth.tsx` — verifica sessão via `/auth/me`. Usa `ENDPOINTS` (Wave 5).
- **Tema:** Contexto `ThemeProvider` em `src/lib/theme.tsx` — persiste preferência em `localStorage` (chave `sog-theme`).
- **Endpoints:** Constantes centralizadas em `src/lib/endpoints.ts` (Wave 5). Nunca usar strings mágicas de API.
- **Formatters:** `src/lib/formatters.ts` com `parseValorMonetario()` — remove `R$`, pontos de milhar, troca vírgula por ponto. Retorna `0` para input vazio/inválido — Wave 2.
- **Tipos:** `src/types/processo.ts` com interfaces `Processo`, `ProcessoHistorico`, `ProcessoCompleto`, `DadosProcesso`, etc. (Wave 5).
- **Pages:** Fila, Detalhe, Historico, Login — todas em `src/pages/`. Detalhe e Historico são lazy-loaded (Wave 5).

---

## Gotchas de CSS / framework

- **React Router v6:** NÃO usar `<Routes>` aninhados. Use `<Outlet />` + rotas filhas.
- **Axios com cookies:** Todas as requisições usam `withCredentials: true` para cookies httpOnly.
- **Base URL da API:** `/api/v1`.
- **Lazy loading:** `React.lazy` + `Suspense` com `Skeleton` como fallback para Detalhe e Historico.
- **ErrorBoundary:** Envolve `<Routes>` no App.tsx. Qualquer erro de renderização mostra UI de fallback com botão "Recarregar página".
- **Filtro client-side:** `Fila.tsx` usa `useMemo` com `filtrarProcessos()` — normaliza número removendo `\D` antes de comparar. Avaliar server-side se fila > 200 processos.

---

## Débitos de UI identificados

- Nenhum teste escrito para `Historico.tsx` (cobertura 0%, mas média global > 60%).
- `App.tsx` e `main.tsx` não cobertos por testes (cobertura 0% nesses arquivos).
- React Router v6 future flags warnings (não crítico, não quebra funcionalidade).
- **Ressalvas do Reviewer — Wave 2 (corrigidas na Wave 3):**
  - `CompensacaoTable.tsx` linha 42: dupla nomenclatura `numero_guia || numeroGuia` indica inconsistência no schema/tipagem. Avaliar padronizar no backend e remover fallback no frontend.
  - `usePollingStatus.ts`: não há timeout máximo de polling. Se o processo ficar preso em `aprovado` indefinidamente, o polling continua até o unmount. Considerar `maxRetries` ou timeout de segurança.
  - `EmissaoStatus.tsx` `useEffect` depende de `data` inteiro (objeto) em vez de apenas `data?.processo.status`, o que pode causar re-runs desnecessários a cada resposta do poll.
  - `parseValorMonetario` não lida com valores já numéricos ou formatações inesperadas (ex: `1.234,56` com ponto de milhar). Threshold de R$ 50.000 está hardcoded em `AvisosAlert.tsx`; não há configuração via env ou API.
- **Correções pós-Review — Wave 3:**
  - Botão exportar: alterado de `window.location.href` para `api.get(blob)` com `responseType: 'blob'`, garantindo refresh token automático — `BotaoExportar.tsx`.
  - Rate limit do endpoint de exportação reduzido para `10/minute`.

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

### Wave 1 — Features Essenciais do Dashboard (2026-05-15)
- **Logs de execução:** Criado `LogsTimeline.tsx` — timeline vertical com bolinhas coloridas (ok=verde, erro=vermelho, aviso=amarelo). Ordenação decrescente por `criado_em`. Badge `aria-hidden` no indicador visual.
- **Tentativas e erro_msg:** `Fila.tsx` exibe `tentativas` nos cards quando > 0. Cards com `erro_msg` ganham borda `border-destructive/50` e fundo `bg-destructive/5`. `ErroBanner.tsx` renderiza `Alert` variant destructive no topo do detalhe quando `processo.erro_msg` existe.
- **Resumo do Preenchimento Automático:** `ResumoPreenchimento.tsx` consolida em grid 4 colunas: sucumbente, contagem de peças (soma de IDs separados por vírgula), quantidade de itens da guia, valor total.
- **Busca client-side:** `BuscaProcesso.tsx` input controlado com ícone de lupa e botão limpar. `Fila.tsx` aplica `filtrarProcessos()` via `useMemo`, normalizando número (remove `\D`) antes de `includes`. Exibe card vazio quando nenhum resultado.
- **Link PJE:** `LinkPje.tsx` monta URL `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso={numero}` com `encodeURIComponent`. Abre em nova aba (`target="_blank" rel="noopener noreferrer"`).
- **Testes:** 41/41 testes passando. Novos arquivos de teste: `LogsTimeline.test.tsx` (6), `ErroBanner.test.tsx` (1), `ResumoPreenchimento.test.tsx` (3), `LinkPje.test.tsx` (3), `BuscaProcesso.test.tsx` (5).

### Wave 2 — Confiança na Aprovação (2026-05-15)
- **Documentos PJE:** `DocumentosPje.tsx` renderiza tabela com `tipo`, `data_assinatura` (formatado via `toLocaleDateString('pt-BR')`) e `nome`. Estado vazio: "Nenhum documento extraído".
- **Compensação:** `CompensacaoTable.tsx` exibe tabela com fallback para snake_case/camelCase em guia de origem. Estado vazio: "Nenhuma compensação".
- **Status da emissão com polling:** `usePollingStatus.ts` faz GET em `ENDPOINTS.PROCESSOS/{id}` a cada 5s. Para quando status ≠ 'aprovado'. `EmissaoStatus.tsx` consome o hook e renderiza spinner, card de sucesso (com toast) ou card de erro (com `erro_msg`).
- **Avisos de valor alto:** `AvisosAlert.tsx` usa `parseValorMonetario` para comparar com threshold de R$ 50.000. Alerta agrupado com outros avisos em lista `ul` dentro de `Alert`.
- **Testes:** 86/86 testes passando. Novos arquivos de teste: `DocumentosPje.test.tsx`, `CompensacaoTable.test.tsx`, `EmissaoStatus.test.tsx`, `usePollingStatus.test.ts`, `formatters.test.ts`.

### Wave 3 — Produtividade (2026-05-15)
- **PDF do demonstrativo:** `DemonstrativoLink.tsx` faz HEAD request para verificar existência do PDF antes de habilitar o link. URL via API `/api/v1/processos/{id}/demonstrativo`. Desabilitado com tooltip "PDF não disponível" quando 404.
- **Paginação no histórico:** `Paginacao.tsx` com controles "Anterior / Próximo", 20 registros por página. Estado gerenciado no `Historico.tsx` via `useState`.
- **Filtros no histórico:** `FiltrosHistorico.tsx` com selects de status (emitido/rejeitado), data (7/30/90 dias) e input de valor mínimo. Filtros combinados via `useMemo` sobre `historico` carregado.
- **Indicadores de prioridade:** `PrioridadeBadge.tsx` renderiza badges com variantes: `urgente` (erro — destructive), `alto_valor` (> R$ 50k — warning), `antigo` (> 7 dias — muted). Consumido nos cards de `Fila.tsx`.
- **Exportação CSV:** `BotaoExportar.tsx` dispara `api.get` com `responseType: 'blob'` e cria objeto URL para download. Inclui nome do arquivo com timestamp. Rate limit do endpoint: `10/minute`.
- **Testes:** 124/124 testes passando. Novos arquivos de teste: `DemonstrativoLink.test.tsx`, `Paginacao.test.tsx`, `FiltrosHistorico.test.tsx`, `PrioridadeBadge.test.tsx`, `BotaoExportar.test.tsx`.

### Fase 1.2 — Agente como Serviço Longo: Barra de Status (2026-05-17)
- **AgenteStatusBar:** Criado `src/components/agente/AgenteStatusBar.tsx` com bolinha colorida (verde=executando/dormindo, amarelo=aguardando_login, cinza=parado/desconhecido, vermelho=erro, azul=autenticando/iniciando), label, mensagem informativa, botões Iniciar/Parar com estados de loading, polling automático a cada 5s via `setInterval` com cleanup no unmount.
- **Endpoints:** Adicionados `AGENTE_INICIAR`, `AGENTE_PARAR`, `AGENTE_STATUS` em `src/lib/endpoints.ts`.
- **Integração:** `<AgenteStatusBar />` incluído no topo da página `Fila.tsx`, antes do `BuscaProcesso`.
- **Acessibilidade:** `role="region"`, `aria-label` nos botões, `aria-hidden` na bolinha decorativa.
- **Estados de UI:** loading nos botões, tratamento gracioso de erro da API (status vira 'desconhecido', online=false), toast em erro de comando.
- **Build e testes:** Build passa sem erros (`npm run build`). 124/124 testes existentes continuam passando.
