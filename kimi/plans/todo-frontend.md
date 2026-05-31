# Plano Técnico — Melhorias do Dashboard Frontend

> Plano formal de implementação das 14 features do `docs/TODO_frontend.md`.
> Revisado e priorizado em 3 waves incrementais, com foco imediato na Wave 1.
> Baseado no codebase atual: React 18 + Vite + Tailwind + React Router v6 + Vitest/RTL.
>
> **Versão:** 1.0-revisado  
> **Data:** 2026-05-15  
> **Autor:** CTO — Fábrica de Software SOG

---

## 1. Visão Geral da Solução

As 14 features são implementadas em **3 waves incrementais**, priorizadas por valor operacional e risco. Cada wave é um conjunto de mudanças **puramente aditivas** no frontend — nenhuma reescrita de módulo existente.

**Estado da API:**
- A API já retorna todos os dados necessários para as Waves 1 e 2 (logs, documentos, compensação, tentativas, erro_msg).
- Apenas a **exportação CSV (W3-F14)** exige novo endpoint na API.
- NÃO existe endpoint de exportar CSV atualmente.

**Estado dos Testes:**
- 12 testes unitários passando (3 arquivos em `frontend/src/__tests__/`).
- Meta de cobertura: manter 12 existentes passando e adicionar testes para todo componente novo.

**Nota sobre status de emissão:**
O TODO menciona `erro_emissao`, mas o schema do banco e o emissor usam `erro`. O frontend deve tratar o status `erro` como estado de falha na emissão.

---

## 2. Wave 1 — Essencial para Operar (Prioridade Imediata)

**Objetivo:** Permitir que o operador revise, busque e entenda um processo sem precisar interpretar dados brutos. Sem essas 5 features, o dashboard não é operacional para o time de custas.

**Tempo estimado:** 2–3 dias de desenvolvimento  
**Risco:** Baixo — todas as dependências de dados já existem na API.

---

### W1-F1: Exibir logs de execução no detalhe do processo

**Descrição do usuário:**
Mostrar `logs` retornados pela API (`/processos/{id}`) em uma timeline vertical com etapa, status (ok/erro/aviso), mensagem e timestamp. Destacar erros em vermelho.

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/LogsTimeline.tsx`
- **Criar:** `frontend/src/components/detalhe/LogsTimeline.test.tsx`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar interface `Log`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar `logs: Log[]` e `documentos: Documento[]` em `ProcessoCompleto`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir `<LogsTimeline logs={dados.logs} />`

**Interface TypeScript:**
```typescript
// frontend/src/types/processo.ts
export interface Log {
  id: number
  processo_id: number
  etapa: string
  status: 'ok' | 'erro' | 'aviso'
  mensagem?: string
  criado_em: string
}

// Atualizar ProcessoCompleto
export interface ProcessoCompleto {
  processo: Processo
  dados: DadosProcesso
  logs: Log[]
  documentos: Documento[]
}
```

**Decisão de UX — ordenação:**
- **Escolha: mais recente no topo.** O operador quer ver o erro atual primeiro, não rolar até o fim. Ordenar por `criado_em` DESC.
- **Reversibilidade:** alta. Ordenação é uma chamada `.sort()` — trivial de inverter.

**Contrato visual:**
- Timeline vertical com linha conectando os itens (border-l-2 com espaçamento).
- Cada item: bolinha colorida (`ok` = verde `bg-green-500`, `erro` = vermelho `bg-destructive`, `aviso` = amarelo `bg-yellow-500`) + `etapa` em negrito + `mensagem` em texto normal + timestamp formatado `pt-BR`.
- Erros (`status === 'erro'`) com fundo `bg-destructive/10` e texto `text-destructive` no container do item.
- Se `logs.length === 0`, mostrar "Nenhum log registrado" em texto muted.
- Card com título "Logs de Execução".

**Critérios de aceite mensuráveis:**
- [ ] Timeline renderiza todos os logs retornados pela API
- [ ] Logs com `status: 'erro'` têm destaque visual vermelho (fundo + texto)
- [ ] Logs ordenados do mais recente para o mais antigo
- [ ] Estado vazio exibe mensagem "Nenhum log registrado"
- [ ] Teste: mock de 3 logs (ok, erro, aviso) verifica renderização, cores e ordenação

---

### W1-F2: Exibir tentativas e erro_msg

**Descrição do usuário:**
Mostrar campo `tentativas` no card do processo na fila. Se `erro_msg` estiver preenchido, exibir alerta visível. Status `erro` deve aparecer na fila com destaque.

**Arquivos:**
- **Modificar:** `frontend/src/types/processo.ts` — adicionar `tentativas?: number`, `erro_msg?: string` em `Processo`
- **Modificar:** `frontend/src/pages/Fila.tsx` — exibir tentativas e alerta de erro nos cards
- **Modificar:** `frontend/src/pages/Fila.test.tsx` — adicionar testes para tentativas e erro_msg
- **Criar:** `frontend/src/components/detalhe/ErroBanner.tsx`
- **Criar:** `frontend/src/components/detalhe/ErroBanner.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir `<ErroBanner />` quando `processo.erro_msg` existir

**Interface TypeScript:**
```typescript
// frontend/src/types/processo.ts
export interface Processo {
  id: number
  numero: string
  status: string
  criado_em: string
  tentativas?: number
  erro_msg?: string
}
```

**Contrato visual (Fila):**
- No card de cada processo, abaixo do número: "Tentativas: N" (texto `text-muted-foreground`, só exibe se `tentativas > 0`).
- Se `erro_msg` preenchido: card com borda `border-destructive/50 bg-destructive/5` + Badge `variant="destructive"` com texto "Erro" ao lado do número do processo.
- A seção "Pendente Manual" já tem destaque visual (`border-warning/50 bg-warning/5`); processos com `erro_msg` usam o padrão destrutivo independentemente da seção.

**Contrato visual (Detalhe):**
- Se `processo.erro_msg` preenchido: `<ErroBanner mensagem={erro_msg} />` no topo da página, abaixo do título "Processo {numero}".
- Banner usa `Alert variant="destructive"` com ícone SVG de alerta (⚠️) e título "Erro na execução".

**Critérios de aceite mensuráveis:**
- [ ] Cards na fila mostram "Tentativas: N" quando `tentativas > 0`
- [ ] Cards com `erro_msg` têm borda vermelha e badge "Erro"
- [ ] Detalhe exibe banner vermelho com mensagem de erro quando `erro_msg` existe
- [ ] Banner de erro não renderiza quando `erro_msg` é undefined/vazio
- [ ] Testes: mock com/sem `erro_msg` e `tentativas` verifica presença/ausência dos elementos

---

### W1-F3: Criar "Resumo do Preenchimento Automático"

**Descrição do usuário:**
Card compacto no topo do detalhe com sucumbente selecionado, peças marcadas (contagem por tipo), itens da guia incluídos e valor total calculado. Evita que o operador decifre dados brutos.

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/ResumoPreenchimento.tsx`
- **Criar:** `frontend/src/components/detalhe/ResumoPreenchimento.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir `<ResumoPreenchimento />` logo após o cabeçalho do título, antes do grid principal

**Decisão de UX — posicionamento:**
- **Escolha: card em largura total acima das duas colunas.** O resumo é a primeira coisa que o operador deve ver ao abrir o detalhe. Colocar dentro do grid quebra a hierarquia visual.
- **Reversibilidade:** alta. É apenas um componente inserido no JSX — mover de lugar é trivial.

**Dados a exibir:**
- **Sucumbente selecionado:** `dados.sucumbente_nome` (ou "Não identificado" se vazio/null)
- **Peças marcadas:** contagem total derivada dos campos `ids_*`. Cada campo é uma string de IDs separados por vírgula. Contar vírgulas + 1 quando o campo não está vazio. Exibir como "7 peças" (total geral) ou detalhado: "Ofícios: 3, Alvarás: 1...".
- **Itens da guia:** contagem de `dados.outros_itens?.length` (ou "Nenhum")
- **Valor total:** `dados.valor_total_recolher` (reaproveitar formatação existente, similar ao `ValorTotal`)

**Contrato visual:**
- Card com título "Resumo do Preenchimento Automático".
- Grid 4 colunas em desktop (`grid-cols-4`), 2 colunas em tablet (`md:grid-cols-2`), 1 coluna em mobile.
- Cada célula: label em `text-muted-foreground text-sm` + valor em `text-lg font-semibold`.
- Dados ausentes exibem "-" ou "Não identificado" em tom muted.

**Critérios de aceite mensuráveis:**
- [ ] Exibe sucumbente, contagem de peças, itens da guia e valor total
- [ ] Trata dados ausentes com "-" ou "Não identificado"
- [ ] Contagem de peças soma todos os tipos (ofícios, alvarás, traslados, mandados, cartas sentença, AR, ARMP)
- [ ] Teste: mock completo verifica todos os 4 campos renderizados
- [ ] Teste: mock incompleto (sem sucumbente, sem peças) verifica estados vazios

---

### W1-F4: Busca por número de processo na fila

**Descrição do usuário:**
Input de busca no topo da Fila que filtra em tempo real por número de processo.

**Arquivos:**
- **Criar:** `frontend/src/components/fila/BuscaProcesso.tsx`
- **Criar:** `frontend/src/components/fila/BuscaProcesso.test.tsx`
- **Modificar:** `frontend/src/pages/Fila.tsx` — adicionar estado de busca e aplicar filtro client-side
- **Modificar:** `frontend/src/pages/Fila.test.tsx` — adicionar teste de filtro

**Decisão de UX — filtro client-side vs server-side:**
- **Escolha: client-side.** A fila é tipicamente pequena (< 100 processos em produção). Latência zero, não gera carga na API e implementação é trivial.
- **Reversibilidade: alta.** Substituir filtro client-side por server-side não quebra contrato — apenas muda de onde os dados vêm. Se a fila crescer além de 200 processos, migrar para query param no endpoint `/processos`.

**Contrato visual:**
- Input com ícone 🔍 (SVG) e placeholder "Buscar por número do processo...".
- Usar componente existente `Input` de `components/ui/Input.tsx`.
- Filtra em tempo real (`onChange`) comparando substring case-insensitive contra `processo.numero`.
- Se nenhum resultado em nenhuma das duas seções: mensagem "Nenhum processo encontrado para esta busca".
- Filtro aplica-se a ambas as seções (Aguardando Aprovação + Pendente Manual) simultaneamente.
- Botão "Limpar" (×) dentro do input quando houver texto.

**Critérios de aceite mensuráveis:**
- [ ] Input renderiza no topo da página, acima das duas seções
- [ ] Digitar número parcial filtra a lista em tempo real (< 100ms de feedback)
- [ ] Busca case-insensitive e funciona com/sem máscara
- [ ] Estado vazio exibe mensagem apropriada quando nenhum processo corresponde
- [ ] Botão "Limpar" reseta o filtro
- [ ] Teste: digita texto e verifica que apenas processos correspondentes aparecem em ambas as seções

---

### W1-F5: Link direto para o PJE

**Descrição do usuário:**
No detalhe do processo, botão "Abrir no PJE" com URL montada para consulta direta.

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/LinkPje.tsx`
- **Criar:** `frontend/src/components/detalhe/LinkPje.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir `<LinkPje />` ao lado do botão "Voltar" no cabeçalho

**Decisão de UX — abrir em nova aba:**
- **Escolha: `target="_blank"` + `rel="noopener noreferrer"`.** O operador precisa manter o dashboard aberto para referência enquanto consulta o PJE. Redirecionar na mesma aba quebra o fluxo de trabalho.
- **Risco:** CSP (Content-Security-Policy) do nginx pode bloquear links externos. Verificar header `Content-Security-Policy` em `nginx/nginx.conf`.

**Contrato visual:**
- Botão secundário (`variant="outline"`) com ícone 🔗 (SVG) e texto "Abrir no PJE".
- Renderizado no cabeçalho, ao lado do botão "← Voltar".
- URL: `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso={numero}`
- Usar `processo.numero` (com máscara, formato aceito pelo PJE).

**Critérios de aceite mensuráveis:**
- [ ] Botão renderiza no cabeçalho do detalhe, ao lado de "Voltar"
- [ ] URL contém o número do processo corretamente
- [ ] Possui `target="_blank"` e `rel="noopener noreferrer"`
- [ ] Teste: verifica atributo `href` do link e `target="_blank"`

---

## 3. Wave 2 — Confiança na Aprovação

**Objetivo:** Dar ao operador todas as informações necessárias para aprovar com segurança, incluindo documentos extraídos, compensações e status em tempo real da emissão.

**Tempo estimado:** 3–4 dias de desenvolvimento  
**Risco:** Médio — W2-F8 (polling) altera o fluxo de aprovação existente.

---

### W2-F6: Exibir documentos PJE extraídos

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/DocumentosPje.tsx`
- **Criar:** `frontend/src/components/detalhe/DocumentosPje.test.tsx`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar interface `Documento`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir componente

**Interface TypeScript:**
```typescript
export interface Documento {
  id: number
  processo_id: number
  doc_id: string
  tipo: string
  data_assinatura?: string
  nome?: string
}
```

**Contrato visual:**
- Tabela com colunas: Tipo, Data de Assinatura, Nome.
- Se `documentos.length === 0`: "Nenhum documento extraído".
- Data formatada `pt-BR` (ou "-" se ausente).
- Renderizado na coluna da direita, abaixo de AcoesPanel.

**Critérios de aceite:**
- [ ] Renderiza todos os documentos retornados pela API
- [ ] Colunas corretas com dados formatados
- [ ] Estado vazio tratado
- [ ] Teste: mock com 2 documentos verifica renderização

---

### W2-F7: Exibir dados de compensação

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/CompensacaoTable.tsx`
- **Criar:** `frontend/src/components/detalhe/CompensacaoTable.test.tsx`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar interface `Compensacao`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir componente

**Interface TypeScript:**
```typescript
export interface Compensacao {
  data?: string
  valor?: string
  numero_guia?: string
  numeroGuia?: string
}
```

**Contrato visual:**
- Tabela com colunas: Data, Valor, Guia de Origem.
- Usar mesma estrutura de `CustasPagasTable` para consistência visual.
- Tratar ambos os campos `numero_guia` / `numeroGuia` (fallback).
- Se não houver compensações: não renderizar o card (ou renderizar com "Nenhuma compensação").

**Critérios de aceite:**
- [ ] Renderiza compensações com data, valor e guia
- [ ] Trata campos alternativos `numero_guia` / `numeroGuia`
- [ ] Teste: mock com compensações verifica tabela

---

### W2-F8: Status da emissão com polling

**Arquivos:**
- **Criar:** `frontend/src/hooks/usePollingStatus.ts`
- **Criar:** `frontend/src/hooks/usePollingStatus.test.ts`
- **Criar:** `frontend/src/components/detalhe/EmissaoStatus.tsx`
- **Criar:** `frontend/src/components/detalhe/EmissaoStatus.test.tsx`
- **Modificar:** `frontend/src/hooks/useAprovar.ts` — não redirecionar imediatamente; manter na página com polling
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — exibir `<EmissaoStatus />` quando processo.status === 'aprovado'

**Decisão de UX — comportamento pós-aprovação:**
- **Escolha: manter na página de detalhe após aprovar.** O hook `useAprovar` atual redireciona para `/` após sucesso. Para polling, ele deve setar um estado local (via callback ou estado compartilhado) indicando que emissão foi iniciada, e não navegar.
- **Implementação:** `usePollingStatus(id, intervaloMs = 5000)` faz polling em `GET /processos/{id}` e retorna `{ status, loading, error, stop }`.
- Polling para quando: status !== 'aprovado' (ou seja, virou `emitido`, `erro`, ou outro estado final).
- **Segurança:** `clearInterval` obrigatório no cleanup do `useEffect` e quando status mudar.

**Contrato visual:**
- Card com spinner + texto "Emissão em andamento..." quando status é `aprovado`.
- Quando status muda para `emitido`: toast de sucesso + texto "✅ Emitido com sucesso" + botão "Voltar para fila".
- Quando status muda para `erro`: toast de erro + texto "❌ Falha na emissão" + exibir `erro_msg` + botão "Voltar".
- Badge com status atual ao lado do título do processo durante polling.

**Critérios de aceite:**
- [ ] Após aprovar, spinner aparece com texto "Emissão em andamento..."
- [ ] Polling a cada 5s via `usePollingStatus`
- [ ] Toast de sucesso quando status vira `emitido`
- [ ] Toast de erro quando status vira `erro`
- [ ] Polling para automaticamente quando status não é mais `aprovado`
- [ ] Teste: mock de mudança de status verifica transição de estados

---

### W2-F9: Melhorar avisos/alertas no detalhe

**Arquivos:**
- **Modificar:** `frontend/src/components/detalhe/AvisosAlert.tsx`
- **Modificar:** `frontend/src/components/detalhe/AvisosAlert.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — passar `valor_total_recolher` como prop adicional

**Novos avisos a adicionar:**
1. **Área não mapeada** (já existe, manter)
2. **Suspensão de exigibilidade** (já existe, manter)
3. **Sucumbente não identificado** (já existe, manter)
4. **Valor muito alto** (NOVO)

**Decisão de UX — threshold de valor alto:**
- **Escolha: threshold hardcoded no frontend = R$ 50.000,00.** Não existe configuração no banco atual.
- **Parser:** extrair função utilitária `parseValorMonetario(valor: string): number` em `frontend/src/lib/formatters.ts` para converter "R$ 10.000,00" → `10000.00`.
- **Sinalização:** Alerta `variant="warning"` com texto "Valor total muito alto (acima de R$ 50.000) — confira manualmente".
- **Reversibilidade: alta.** Mudar o threshold é alterar uma constante. Extrair para `lib/formatters.ts` centraliza o parser.

**Contrato visual:**
- Cada aviso é um `<li>` com ícone correspondente.
- Valor muito alto: ícone ⚠️ + texto explicativo.
- Card só renderiza se pelo menos um aviso for verdadeiro.

**Critérios de aceite:**
- [ ] Aviso de valor alto aparece quando `valor_total_recolher` > R$ 50.000
- [ ] Parser de valor funciona com formatos "R$ 10.000,00" e "10000,00"
- [ ] Todos os 4 avisos podem aparecer simultaneamente
- [ ] Teste: mock com valor alto verifica presença do aviso

---

## 4. Wave 3 — Produtividade

**Objetivo:** Acelerar o trabalho do operador com navegação eficiente, filtros, exportação e indicadores visuais de prioridade.

**Tempo estimado:** 4–5 dias de desenvolvimento  
**Risco:** Médio-Alto — W3-F14 exige novo endpoint na API.

---

### W3-F10: Preview/link do PDF do demonstrativo

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/DemonstrativoLink.tsx`
- **Criar:** `frontend/src/components/detalhe/DemonstrativoLink.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir na coluna da direita

**Decisão de UX — link vs embed:**
- **Escolha: link para nova aba.** O PDF está em `/dados/demonstrativos/` (servido pelo nginx ou API). Embeds de PDF são problemáticos cross-browser e de segurança. Um link direto com ícone 📄 é mais confiável.
- **URL:** `/dados/demonstrativos/{numero_sem_mascara}_demonstrativo.pdf` (confirmar padrão com backend; se incerto, usar endpoint dedicado).
- **Risco:** A URL `/dados/demonstrativos/` pode não estar exposta pelo nginx. Confirmar mapeamento de volumes antes de implementar.

**Contrato visual:**
- Card com título "Demonstrativo" e botão "Abrir PDF" que abre em nova aba.
- Se arquivo não existe (404): mostrar "PDF não disponível" em texto muted.

**Critérios de aceite:**
- [ ] Link para PDF renderiza no detalhe
- [ ] Abre em nova aba
- [ ] Estado de indisponibilidade tratado
- [ ] Teste: verifica atributo `href` do link

---

### W3-F11: Paginação no histórico

**Arquivos:**
- **Modificar:** `frontend/src/pages/Historico.tsx` — adicionar controles de paginação
- **Criar:** `frontend/src/components/historico/Paginacao.tsx`
- **Criar:** `frontend/src/components/historico/Paginacao.test.tsx`
- **Modificar:** `frontend/src/__tests__/Historico.test.tsx`

**Decisão técnica:**
- O endpoint `/historico` já suporta `?limit=50&offset=0`. Apenas a UI precisa ser implementada.
- **Limite padrão:** 20 registros por página (melhor UX que 50).
- **Controles:** botões "Anterior" / "Próxima" (desabilitados quando não aplicável).

**Contrato visual:**
- Barra abaixo da tabela com: "Mostrando X-Y de Z" + botões Anterior/Próxima.
- Botão desabilitado quando não há página anterior/próxima.

**Critérios de aceite:**
- [ ] Histórico carrega 20 registros por página
- [ ] Botão "Próxima" carrega próxima página via `offset`
- [ ] Botão "Anterior" volta à página anterior
- [ ] Texto informativo de intervalo exibido
- [ ] Teste: mock com 25 registros verifica paginação

---

### W3-F12: Filtros no histórico

**Arquivos:**
- **Modificar:** `frontend/src/pages/Historico.tsx` — adicionar barra de filtros
- **Criar:** `frontend/src/components/historico/FiltrosHistorico.tsx`
- **Criar:** `frontend/src/components/historico/FiltrosHistorico.test.tsx`
- **Modificar:** `frontend/src/__tests__/Historico.test.tsx`

**Decisão de UX — client-side vs server-side:**
- **Escolha: client-side sobre a página atual.** O endpoint `/historico` não tem query params de filtro. Implementar filtros client-side é trivial e totalmente reversível.
- **Mitigação de risco:** filtros aplicam-se sobre a página atual carregada, não sobre todo o dataset. Se o volume de dados crescer, o endpoint pode ser estendido com filtros sem quebrar a UI.
- **Reversibilidade: alta.** Migrar para server-side só requer mover a lógica de filtro para a query string.

**Filtros:**
1. **Status:** select com opções "Todos", "Emitido", "Rejeitado"
2. **Data:** select com opções "Todos", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"
3. **Valor:** input numérico "Valor mínimo (R$)"

**Contrato visual:**
- Barra horizontal acima da tabela com 3 controles.
- Filtros aplicam em conjunto (AND lógico).
- Botão "Limpar filtros" para resetar.
- Paginação reseta para página 1 quando filtro muda.
- Estado vazio atualizado: "Nenhum registro corresponde aos filtros".

**Critérios de aceite:**
- [ ] Filtro por status funciona
- [ ] Filtro por data funciona (comparando `atualizado_em`)
- [ ] Filtro por valor mínimo funciona
- [ ] Filtros combinam com AND
- [ ] Botão "Limpar filtros" reseta tudo
- [ ] Paginação reseta para página 1 quando filtro muda
- [ ] Teste: mock com registros variados verifica cada filtro

---

### W3-F13: Indicadores de prioridade na fila

**Arquivos:**
- **Modificar:** `frontend/src/pages/Fila.tsx` — adicionar lógica de prioridade
- **Criar:** `frontend/src/components/fila/PrioridadeBadge.tsx`
- **Criar:** `frontend/src/components/fila/PrioridadeBadge.test.tsx`
- **Modificar:** `frontend/src/__tests__/Fila.test.tsx`

**Regras de prioridade (ordem de exibição):**
1. **Erro nas tentativas:** se `tentativas > 0 && erro_msg`, badge "Urgente" `variant="destructive"`
2. **Valor alto:** se `valor_total_recolher` > R$ 50.000 (reusar parser de `lib/formatters.ts`), badge "Alto Valor" `variant="warning"`
3. **Processo antigo:** se `criado_em` > 7 dias, badge "Antigo" `variant="secondary"`

**Decisão de UX:**
- Prioridade 1 (Erro) sempre sobrepõe as outras visualmente — card com borda vermelha (`border-destructive/50 bg-destructive/5`).
- Badges aparecem ao lado do número do processo.
- Ordenação da fila: manter ordenação atual (por `criado_em` DESC), apenas adicionar indicadores visuais. Não reordenar para não confundir o operador.

**Critérios de aceite:**
- [ ] Processos com erro exibem badge "Urgente" e borda vermelha
- [ ] Processos com valor > R$ 50.000 exibem badge "Alto Valor"
- [ ] Processos com > 7 dias exibem badge "Antigo"
- [ ] Múltiplos badges podem aparecer no mesmo card
- [ ] Teste: mock com diferentes cenários verifica badges corretos

---

### W3-F14: Exportação do histórico

**Arquivos — Frontend:**
- **Criar:** `frontend/src/components/historico/BotaoExportar.tsx`
- **Criar:** `frontend/src/components/historico/BotaoExportar.test.tsx`
- **Modificar:** `frontend/src/pages/Historico.tsx` — incluir botão

**Arquivos — API (endpoint novo):**
- **Criar/modificar:** `api/src/rotas/historico.py` — adicionar `GET /historico/exportar`
- **Modificar:** `api/src/main.py` — registrar nova rota se necessário

**⚠️ Endpoint novo na API — Reversibilidade: baixa**

**Contrato do endpoint:**
```
GET /api/v1/historico/exportar
Response: text/csv com header Content-Disposition: attachment; filename="historico.csv"
```

**Implementação sugerida (backend):**
```python
from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/exportar")
def exportar_historico(user: str = Depends(get_current_user)):
    # Reutiliza a mesma query do /historico sem limit/offset
    rows = ...  # todos os registros emitidos/rejeitados
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[...])
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=historico.csv"}
    )
```

**Contrato visual (frontend):**
- Botão "📥 Exportar CSV" no topo da página de histórico.
- Clique dispara download via `window.location.href` (simples) ou `fetch` + blob download (mais controle).
- Loading state enquanto gera (spinner no botão).

**Critérios de aceite:**
- [ ] Botão "Exportar CSV" renderiza no histórico
- [ ] Clique faz download de arquivo CSV válido
- [ ] CSV contém colunas: Número, Polo Ativo, Valor Total, Status, Data, Observação
- [ ] Encoding UTF-8 com BOM para acentuação correta no Excel
- [ ] Teste: mock do endpoint verifica chamada e download

---

## 5. Dependências entre Features

```
W1-F1 (Logs) ─────────────────────────┐
W1-F2 (Tentativas/Erro) ──────────────┤
W1-F3 (Resumo) ───────────────────────┤ → Wave 1 (independentes entre si)
W1-F4 (Busca) ────────────────────────┤
W1-F5 (Link PJE) ─────────────────────┘
        ↓
W2-F6 (Documentos) ───────────────────┐
W2-F7 (Compensação) ──────────────────┤ → Wave 2 (independentes entre si)
W2-F8 (Polling emissão) ──────────────┤     W2-F8 depende de W1-F2 (tratamento de erro)
W2-F9 (Avisos) ───────────────────────┘     W2-F9 reusa parser de valor da W3-F13
        ↓
W3-F10 (PDF) ─────────────────────────┐
W3-F11 (Paginação) ───────────────────┤
W3-F12 (Filtros) ─────────────────────┼── → Wave 3
W3-F13 (Prioridade) ──────────────────┤     W3-F12 depende de W3-F11 (paginação)
W3-F14 (Exportar) ────────────────────┘     W3-F14 é independente
```

**Notas sobre dependências:**
- W2-F8 requer que W1-F2 esteja feito para reaproveitar o tratamento de `erro_msg` no estado de emissão falha.
- W2-F9 reusa o parser de valor monetário — recomenda-se implementar `lib/formatters.ts` na W2-F9 (ou antecipar para Wave 1 se conveniente).
- W3-F12 (Filtros) e W3-F11 (Paginação) são melhores entregues juntos: filtros devem resetar paginação para página 1.
- W3-F13 reusa o parser de valor monetário implementado em W2-F9.

---

## 6. Decisões de Baixa Reversibilidade

| Decisão | Justificativa | Reversibilidade |
|---------|---------------|-----------------|
| **Endpoint `/historico/exportar` (CSV)** | Novo endpoint na API. Remover não quebra o frontend (botão pode ser desabilitado), mas introduz contrato permanente. | Baixa — requer depreciação do endpoint se removido |
| **Parser de valor monetário no frontend** | Lógica de parsing "R$ 10.000,00" → número centralizada em `lib/formatters.ts`. Mudar formato requer atualização em um único lugar. | Média — extrair para util mitiga o risco |
| **Polling de emissão (W2-F8)** | Altera o fluxo pós-aprovação (não redireciona imediatamente). Reverter requer apenas restaurar `navigate('/')` no hook. | Alta — mudança localizada em um hook |

---

## 7. Riscos e Pontos de Atenção

1. **Status de emissão:** O TODO menciona `erro_emissao` mas o banco e emissor usam `erro`. O frontend deve usar `erro`. Se futuramente houver um `erro_emissao` específico, o polling já está preparado.

2. **Polling excessivo:** Polling a cada 5s pode gerar carga se muitos operadores aprovarem simultaneamente. O intervalo deve ser cancelado (`clearInterval`) ao desmontar o componente e quando status mudar. Monitorar logs da API após deploy.

3. **Filtros client-side no histórico:** Se o histórico crescer além de ~500 registros, a paginação server-side existente (`limit/offset`) precisa ser combinada com filtros server-side para não paginar dados filtrados incorretamente. **Mitigação:** implementar filtros client-side sobre a página atual, não sobre todo o dataset.

4. **CORS em link para PJE:** O link externo para `pje.tjdft.jus.br` pode ser bloqueado por CSP. Verificar `Content-Security-Policy` do nginx em `nginx/nginx.conf` e `nginx/nginx-dev.conf`.

5. **PDF de demonstrativo:** A URL `/dados/demonstrativos/` pode não estar exposta pelo nginx. Confirmar mapeamento de volumes antes de implementar W3-F10.

6. **Campos opcionais da API:** A API retorna `tentativas`, `erro_msg`, `logs`, `documentos` e `compensacao` como opcionais. O frontend deve tratar todos como opcionais (undefined/null) sem quebrar.

---

## 8. Critérios de Aceite por Wave

### Wave 1 — Aceite
- [ ] Todas as 5 features funcionam em ambiente de desenvolvimento (`docker-compose.dev.yml`)
- [ ] Testes unitários cobrem todos os componentes novos (meta: mínimo 1 teste por componente)
- [ ] Nenhum teste existente quebra (12/12 passando)
- [ ] Filtro de busca responde em < 100ms para fila com 50 processos
- [ ] Plano de rollback: remover componentes do JSX de `Detalhe.tsx` e `Fila.tsx` reverte todas as mudanças

### Wave 2 — Aceite
- [ ] Todas as 4 features funcionam em ambiente de desenvolvimento
- [ ] Polling de emissão para corretamente quando processo muda de status
- [ ] Aviso de valor alto dispara apenas para valores > R$ 50.000
- [ ] Documentos e compensação renderizam com dados reais da API
- [ ] Parser de valor monetário está centralizado em `lib/formatters.ts`

### Wave 3 — Aceite
- [ ] Todas as 5 features funcionam em ambiente de desenvolvimento
- [ ] Paginação carrega próxima página em < 500ms
- [ ] Exportação CSV gera arquivo válido com acentuação correta no Excel
- [ ] Prioridade na fila reflete regras de negócio definidas
- [ ] Cobertura de testes mantida (todos os testes passando)

---

## 9. Checklist de Entrega Final

- [ ] Plano técnico revisado e salvo em `.kimi/plans/todo-frontend.md`
- [ ] Cada feature mapeada para wave específica com arquivos e interfaces
- [ ] Critérios de aceite mensuráveis por wave
- [ ] Nenhuma reescrita completa de módulos — apenas adições e modificações cirúrgicas
- [ ] Abordagens preferencialmente reversíveis (client-side primeiro, endpoints novos sinalizados)
- [ ] Endpoint novo sinalizado explicitamente (W3-F14)
- [ ] Riscos mapeados com mitigações
- [ ] Decisões de UX documentadas com justificativas
