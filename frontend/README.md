# Frontend — Dashboard SOG

Interface React do Sistema de Ordem de Guias. Dashboard para revisão e aprovação humana de guias de custas processuais extraídas automaticamente do PJE.

## Stack

- React 18 + TypeScript
- Vite 5
- Tailwind CSS v4
- React Router v6
- Axios

## Dev Local

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
npm test
```

## Features do Dashboard

### Wave 1 — Operação Essencial

1. **Logs de Execução no Detalhe** — Timeline vertical colorida (ok/erro/aviso) exibindo etapas, mensagens e timestamps dos logs do processo.

2. **Tentativas e Mensagem de Erro** — Contador de tentativas exibido nos cards da fila. Quando `erro_msg` está presente, um banner de alerta vermelho aparece no topo do detalhe e o card na fila ganha borda destacada.

3. **Resumo do Preenchimento Automático** — Card compacto no topo do detalhe consolidando: sucumbente identificado, quantidade de peças marcadas, itens da guia e valor total calculado.

4. **Busca por Número de Processo** — Filtro client-side na fila com busca em tempo real (ignora caracteres não numéricos). Exibe estado vazio quando nenhum resultado é encontrado.
   > **Nota:** A busca é client-side. Se a fila ultrapassar ~200 processos, avaliar migração para server-side.

5. **Link Direto para o PJE** — Botão "Abrir no PJE" no detalhe do processo que abre a consulta do processo no PJE em nova aba, com URL montada dinamicamente a partir do número do processo.

### Wave 2 — Confiança na Aprovação

1. **Documentos PJE Extraídos** — Tabela em card com tipo, data de assinatura e nome dos documentos retornados pela API (`documentos` no payload do processo). Estado vazio exibido quando não há documentos.

2. **Dados de Compensação** — Tabela em card com data, valor e guia de origem (`compensacao` do banco, JSON array). Suporta ambas as chaves `numero_guia` (snake_case) e `numeroGuia` (camelCase) para compatibilidade com schemas legados.

3. **Status da Emissão com Polling** — Após aprovar, o componente `EmissaoStatus` exibe spinner "Emissão em andamento..." e dispara o hook `usePollingStatus` que consulta a API a cada 5s. Quando o status muda de `aprovado` para `emitido` ou `erro`, o polling para automaticamente e um toast de sucesso/erro é exibido. Botão "Voltar para fila" disponível nos estados finais.
   > **Hook `usePollingStatus`:** Recebe `id` do processo e `intervaloMs` (default 5000). Faz fetch imediato ao montar, agenda `setInterval` e expõe `stop()` para cancelamento manual. Cleanup automático no unmount via `useEffect`.

4. **Avisos de Valor Alto** — Alerta visível no detalhe quando `valor_total_recolher > R$ 50.000`, calculado via `parseValorMonetario` em `src/lib/formatters.ts`. Agrupado com outros avisos (área não mapeada, suspensão de exigibilidade, sucumbente não identificado) no componente `AvisosAlert`.

### Wave 3 — Produtividade

1. **PDF do Demonstrativo** — Link `DemonstrativoLink` no detalhe que verifica disponibilidade do PDF via HEAD request antes de habilitar o clique. URL aponta para `/dados/demonstrativos/{numero_processo}.pdf` via endpoint da API.

2. **Paginação no Histórico** — Componente `Paginacao` aplicado ao `Historico.tsx`, exibindo 20 registros por página. Controles "Anterior / Próximo" com estado de página atual.
   > **Nota:** A paginação é client-side. Se o histórico ultrapassar ~500 registros, avaliar migração para server-side com `limit/offset`.

3. **Filtros no Histórico** — Painel `FiltrosHistorico` com filtros por status (emitido / rejeitado), data (últimos 7, 30 ou 90 dias) e valor mínimo. Filtros aplicados em conjunto via `useMemo` sobre a lista carregada.
   > **Nota:** Os filtros são client-side. Para grandes volumes, migrar para server-side.

4. **Indicadores de Prioridade** — Badges `PrioridadeBadge` nos cards da fila com três níveis: **Urgente** (processo com erro nas tentativas — vermelho), **Alto Valor** (> R$ 50.000 — amarelo) e **Antigo** (> 7 dias na fila — cinza). Permite ao operador identificar rapidamente o que precisa de atenção.

5. **Exportação CSV** — Botão `BotaoExportar` no histórico que faz download via `api.get(blob)` com `responseType: 'blob'`. O fluxo inclui refresh token automático via interceptor, garantindo que a exportação não falhe por token expirado. Endpoint com rate limit de `10/minute`.
