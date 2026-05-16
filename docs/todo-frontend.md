# Plano Técnico — Melhorias de UX no Dashboard (TODO_frontend.md)

> Decomposição das 14 features do `docs/TODO_frontend.md` em waves incrementais verificáveis.
> Baseado no codebase atual: React 18 + Vite + Tailwind + React Router v6 + Vitest/RTL.

---

## Visão Geral da Solução

As 14 features são implementadas em **3 waves incrementais**, priorizadas por valor operacional. Cada wave é um conjunto de mudanças puramente aditivas no frontend — nenhuma reescrita de módulo. A API já retorna todos os dados necessários para as Waves 1 e 2; apenas a **exportação CSV (item 14)** exige novo endpoint na API. Filtros de histórico são implementados client-side inicialmente (reversível e rápido), com caminho de migração para server-side se o volume de registros crescer.

**Nota importante sobre status de emissão:** O TODO menciona `erro_emissao`, mas o schema do banco e o emissor usam `erro`. O frontend deve tratar o status `erro` como estado de falha na emissão.

---

## Wave 1 — Essencial para Operar (5 features)

**Objetivo:** Permitir que o operador revise, busque e entenda um processo sem precisar interpretar dados brutos.

### W1-F1: Exibir logs de execução no detalhe do processo

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/LogsTimeline.tsx`
- **Criar:** `frontend/src/components/detalhe/LogsTimeline.test.tsx`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar interface `Log`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir `<LogsTimeline />`

**Interface:**
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

**Contrato visual:**
- Timeline vertical com itens ordenados por `criado_em` DESC (mais recente no topo)
- Cada item: bolinha colorida (`ok` = verde, `erro` = vermelho, `aviso` = amarelo) + `etapa` + `mensagem` + timestamp formatado `pt-BR`
- Erros (`status === 'erro'`) com fundo `bg-destructive/10` e texto `text-destructive`
- Se `logs.length === 0`, mostrar "Nenhum log registrado"

**Critérios de aceite:**
- [ ] Timeline renderiza todos os logs retornados pela API
- [ ] Logs com `status: 'erro'` têm destaque visual vermelho
- [ ] Logs ordenados do mais recente para o mais antigo
- [ ] Teste: mock de 3 logs (ok, erro, aviso) verifica renderização e cores

---

### W1-F2: Exibir tentativas e erro_msg

**Arquivos:**
- **Modificar:** `frontend/src/types/processo.ts` — `tentativas?: number`, `erro_msg?: string` em `Processo`
- **Modificar:** `frontend/src/pages/Fila.tsx` — exibir tentativas e alerta de erro
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — exibir banner de erro_msg no topo
- **Criar:** `frontend/src/components/detalhe/ErroBanner.tsx`
- **Criar:** testes em `Fila.test.tsx` e `Detalhe.test.tsx`

**Contrato visual (Fila):**
- No card de cada processo, abaixo do número: "Tentativas: N" (texto muted, só exibe se `tentativas > 0`)
- Se `erro_msg` preenchido: card com borda `border-destructive/50 bg-destructive/5` + Badge `variant="destructive"` com texto "Erro"
- Na seção "Pendente Manual" já existe destaque; aplicar o mesmo padrão para processos com `erro_msg`

**Contrato visual (Detalhe):**
- Se `processo.erro_msg` preenchido: `<ErroBanner mensagem={erro_msg} />` no topo da página, abaixo do título
- Banner usa `Alert variant="destructive"` com ícone ⚠️

**Critérios de aceite:**
- [ ] Cards na fila mostram tentativas quando > 0
- [ ] Cards com `erro_msg` têm borda vermelha e badge "Erro"
- [ ] Detalhe exibe banner vermelho com mensagem de erro quando `erro_msg` existe
- [ ] Testes: mock com/sem erro_msg verifica presença/ausência dos elementos

---

### W1-F3: Criar "Resumo do Preenchimento Automático"

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/ResumoPreenchimento.tsx`
- **Criar:** `frontend/src/components/detalhe/ResumoPreenchimento.test.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir logo após o título

**Dados a exibir:**
- **Sucumbente selecionado:** `dados.sucumbente_nome` (ou "Não identificado" se vazio)
- **Peças marcadas:** contagem por tipo derivada dos campos `ids_*` (ex: "Ofícios: 3, Alvarás: 1" ou apenas total)
- **Itens da guia:** contagem de `dados.outros_itens?.length` (ou "Nenhum")
- **Valor total:** `dados.valor_total_recolher` (componente existente `ValorTotal` pode ser reaproveitado ou movido para cá)

**Contrato visual:**
- Card compacto com grid 2 colunas (mobile: 1 coluna)
- Cada linha: label muted + valor em destaque
- Título do card: "Resumo do Preenchimento Automático"

**Critérios de aceite:**
- [ ] Exibe sucumbente, contagem de peças, itens da guia e valor total
- [ ] Trata dados ausentes com "-" ou "Não identificado"
- [ ] Teste: mock completo e mock incompleto verificam renderização correta

---

### W1-F4: Busca por número de processo na fila

**Arquivos:**
- **Modificar:** `frontend/src/pages/Fila.tsx` — adicionar input de busca
- **Criar:** `frontend/src/components/fila/BuscaProcesso.tsx`
- **Criar:** `frontend/src/components/fila/BuscaProcesso.test.tsx`
- **Modificar:** `frontend/src/pages/Fila.tsx` — aplicar filtro client-side

**Decisão de UX — filtro client-side vs server-side:**
- **Escolha: client-side.** A fila é tipicamente pequena (< 100 processos). Latência zero e implementação trivial. Se a fila crescer além de 200 processos, migrar para query param no endpoint `/processos`.
- **Reversibilidade: alta.** Substituir filtro client-side por server-side não quebra contrato — apenas muda de onde os dados vêm.

**Contrato visual:**
- Input com ícone 🔍 e placeholder "Buscar por número do processo..."
- Filtra em tempo real (`onChange`) comparando substring case-insensitive contra `processo.numero` (com e sem máscara, se necessário usar `numero_sem_mascara`)
- Se nenhum resultado: mensagem "Nenhum processo encontrado para esta busca"
- Filtro aplica-se a ambas as seções (Aguardando Aprovação + Pendente Manual)

**Critérios de aceite:**
- [ ] Input renderiza no topo da página
- [ ] Digitar número parcial filtra a lista em tempo real
- [ ] Busca case-insensitive e funciona com/sem máscara
- [ ] Estado vazio exibe mensagem apropriada
- [ ] Teste: digita texto e verifica que apenas processos correspondentes aparecem

---

### W1-F5: Link direto para o PJE

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/LinkPje.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir ao lado do botão "Voltar"

**Contrato visual:**
- Botão secundário (outline) com ícone 🔗 e texto "Abrir no PJE"
- URL: `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso={numero}`
- `target="_blank"` + `rel="noopener noreferrer"`
- Usar `processo.numero` (com máscara, formato aceito pelo PJE)

**Critérios de aceite:**
- [ ] Botão renderiza no cabeçalho do detalhe
- [ ] URL contém o número do processo corretamente
- [ ] Abre em nova aba
- [ ] Teste: verifica atributo `href` do link

---

## Wave 2 — Confiança na Aprovação (4 features)

**Objetivo:** Dar ao operador todas as informações necessárias para aprovar com segurança.

### W2-F6: Exibir documentos PJE extraídos

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/DocumentosPje.tsx`
- **Criar:** `frontend/src/components/detalhe/DocumentosPje.test.tsx`
- **Modificar:** `frontend/src/types/processo.ts` — adicionar interface `Documento`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir componente

**Interface:**
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
- Tabela com colunas: Tipo, Data de Assinatura, Nome
- Se `documentos.length === 0`: "Nenhum documento extraído"
- Data formatada `pt-BR` (ou "-" se ausente)

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

**Interface:**
```typescript
export interface Compensacao {
  data?: string
  valor?: string
  numero_guia?: string
  numeroGuia?: string
}
```

**Contrato visual:**
- Tabela com colunas: Data, Valor, Guia de Origem
- Usar mesma estrutura de `CustasPagasTable` para consistência
- Estado vazio: não renderizar o card (ou renderizar com "Nenhuma compensação")

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
- **Modificar:** `frontend/src/hooks/useAprovar.ts` — após aprovar, não redirecionar imediatamente; manter na página com polling
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — exibir `<EmissaoStatus />` quando processo.status === 'aprovado'

**Decisão de UX — comportamento pós-aprovação:**
- **Escolha: manter na página de detalhe após aprovar.** O hook `useAprovar` atual redireciona para `/` após sucesso. Para polling, ele deve:
  1. Setar um estado local `emissaoIniciada = true`
  2. Navegar para `/` apenas quando status for `emitido` ou `erro`
  3. Ou, alternativa mais simples: manter na página e o polling roda localmente
- **Implementação:** `usePollingStatus(id, intervaloMs)` faz polling em `GET /processos/{id}` a cada 5s e retorna `{ status, loading, stop }`
- Polling para quando: status !== 'aprovado' (ou seja, virou `emitido`, `erro`, ou outro)

**Contrato visual:**
- Card com spinner + texto "Emissão em andamento..."
- Quando status muda para `emitido`: toast de sucesso + texto "✅ Emitido com sucesso" + botão "Voltar para fila"
- Quando status muda para `erro`: toast de erro + texto "❌ Falha na emissão" + exibir `erro_msg` + botão "Voltar"
- Badge com status atual ao lado do título do processo

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
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — passar props adicionais

**Novos avisos a adicionar:**
1. **Área não mapeada** (já existe, manter)
2. **Suspensão de exigibilidade** (já existe, manter)
3. **Sucumbente não identificado** (já existe, manter)
4. **Valor muito alto** (NOVO)

**Decisão de UX — threshold de valor alto:**
- **Escolha: threshold hardcoded no frontend = R$ 50.000,00.** Não existe configuração no banco atual. O parser de valor deve limpar "R$", pontos de milhar e substituir vírgula por ponto para comparação numérica.
- **Sinalização:** Alerta `variant="warning"` com texto "Valor total muito alto (acima de R$ 50.000) — confira manualmente"
- **Reversibilidade: alta.** Mudar o threshold é alterar uma constante.

**Contrato visual:**
- Cada aviso é um `<li>` com ícone correspondente
- Valor muito alto: ícone ⚠️ + texto explicativo
- Card só renderiza se pelo menos um aviso for verdadeiro

**Critérios de aceite:**
- [ ] Aviso de valor alto aparece quando `valor_total_recolher` > R$ 50.000
- [ ] Parser de valor funciona com formatos "R$ 10.000,00" e "10000,00"
- [ ] Todos os 4 avisos podem aparecer simultaneamente
- [ ] Teste: mock com valor alto verifica presença do aviso

---

## Wave 3 — Produtividade (5 features)

**Objetivo:** Acelerar o trabalho do operador com navegação eficiente, filtros e exportação.

### W3-F10: Preview/link do PDF do demonstrativo

**Arquivos:**
- **Criar:** `frontend/src/components/detalhe/DemonstrativoLink.tsx`
- **Modificar:** `frontend/src/pages/Detalhe.tsx` — incluir na coluna da direita

**Decisão de UX — link vs embed:**
- **Escolha: link para nova aba.** O PDF está em `/dados/demonstrativos/` (servido pelo nginx ou API). Embeds de PDF são problemáticos cross-browser e de segurança. Um link direto com ícone 📄 é mais confiável.
- **URL:** `/dados/demonstrativos/{numero_sem_mascara}_demonstrativo.pdf` (confirmar padrão com backend; se incerto, usar endpoint dedicado)

**Contrato visual:**
- Card com título "Demonstrativo" e botão "Abrir PDF" que abre em nova aba
- Se arquivo não existe (404): mostrar "PDF não disponível" em texto muted

**Critérios de aceite:**
- [ ] Link para PDF renderiza no detalhe
- [ ] Abre em nova aba
- [ ] Estado de indisponibilidade tratado
- [ ] Teste: verifica atributo `href` do link

---

### W3-F11: Paginação no histórico

**Arquivos:**
- **Modificar:** `frontend/src/pages/Historico.tsx` — adicionar controles de paginação
- **Modificar:** `frontend/src/pages/Historico.tsx` — usar `limit` e `offset` na chamada API
- **Criar:** `frontend/src/components/historico/Paginacao.tsx`
- **Modificar:** `frontend/src/__tests__/Historico.test.tsx`

**Decisão técnica:**
- O endpoint `/historico` já suporta `?limit=50&offset=0`. Apenas a UI precisa ser implementada.
- **Limite padrão:** 20 registros por página (melhor UX que 50)
- **Controles:** botões "Anterior" / "Próxima" (desabilitados quando não aplicável)

**Contrato visual:**
- Barra abaixo da tabela com: "Mostrando X-Y de Z" + botões Anterior/Próxima
- Botão desabilitado quando não há página anterior/próxima

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
- **Modificar:** `frontend/src/__tests__/Historico.test.tsx`

**Decisão de UX — client-side vs server-side:**
- **Escolha: client-side.** O endpoint `/historico` não tem query params de filtro. Implementar filtros client-side é trivial e totalmente reversível. Se o volume de dados crescer, o endpoint pode ser estendido com filtros sem quebrar a UI.
- **Reversibilidade: alta.** Migrar para server-side só requer mover a lógica de filtro para a query string.

**Filtros:**
1. **Status:** select com opções "Todos", "Emitido", "Rejeitado"
2. **Data:** select com opções "Todos", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"
3. **Valor:** input numérico "Valor mínimo (R$)"

**Contrato visual:**
- Barra horizontal acima da tabela com 3 controles
- Filtros aplicam em conjunto (AND lógico)
- Botão "Limpar filtros" para resetar
- Estado vazio atualizado: "Nenhum registro corresponde aos filtros"

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
- **Modificar:** `frontend/src/__tests__/Fila.test.tsx`

**Regras de prioridade (ordem de exibição):**
1. **Erro nas tentativas:** se `tentativas > 0 && erro_msg`, badge "Urgente" `variant="destructive"`
2. **Valor alto:** se `valor_total_recolher` > R$ 50.000 (usar mesmo parser da W2-F9), badge "Alto Valor" `variant="warning"`
3. **Processo antigo:** se `criado_em` > 7 dias, badge "Antigo" `variant="secondary"`

**Decisão de UX:**
- Prioridade 1 (Erro) sempre sobrepõe as outras visualmente — card com borda vermelha
- Badges aparecem ao lado do número do processo
- Ordenação da fila: manter ordenação atual (por `criado_em` DESC), apenas adicionar indicadores visuais

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
- **Modificar:** `frontend/src/pages/Historico.tsx` — incluir botão
- **Criar:** testes

**Arquivos — API (endpoint novo):**
- **Criar/modificar:** `api/src/rotas/historico.py` — adicionar `GET /historico/exportar`
- **Modificar:** `api/src/schemas.py` — response model (ou usar StreamingResponse)

**⚠️ Endpoint novo na API — Reversibilidade: alta**

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
- Botão "📥 Exportar CSV" no topo da página de histórico
- Clique dispara download via `window.location.href` ou `fetch` + blob download
- Loading state enquanto gera

**Critérios de aceite:**
- [ ] Botão "Exportar CSV" renderiza no histórico
- [ ] Clique faz download de arquivo CSV válido
- [ ] CSV contém colunas: Número, Polo Ativo, Valor Total, Status, Data, Observação
- [ ] Encoding UTF-8 com BOM para acentuação correta no Excel
- [ ] Teste: mock do endpoint verifica chamada e download

---

## Dependências entre Features

```
W1-F1 (Logs) ─────────────────────────┐
W1-F2 (Tentativas/Erro) ──────────────┤
W1-F3 (Resumo) ───────────────────────┤ → Wave 1 (independente)
W1-F4 (Busca) ────────────────────────┤
W1-F5 (Link PJE) ─────────────────────┘
        ↓
W2-F6 (Documentos) ───────────────────┐
W2-F7 (Compensação) ──────────────────┤ → Wave 2 (independente entre si)
W2-F8 (Polling emissão) ──────────────┤     mas W2-F8 depende de W1-F2 (tratamento de erro)
W2-F9 (Avisos) ───────────────────────┘     W2-F9 reusa parser de valor da W3-F13
        ↓
W3-F10 (PDF) ─────────────────────────┐
W3-F11 (Paginação) ───────────────────┤
W3-F12 (Filtros) ─────────────────────┼── → Wave 3
W3-F13 (Prioridade) ──────────────────┤     W3-F12 depende de W3-F11 (paginação)
W3-F14 (Exportar) ────────────────────┘     W3-F14 é independente
```

**Nota sobre dependências:**
- W2-F8 requer que W1-F2 esteja feito para reaproveitar o tratamento de `erro_msg` no estado de emissão falha
- W3-F12 (Filtros) e W3-F11 (Paginação) são melhores entregues juntos: filtros devem resetar paginação para página 1
- W3-F13 reusa o parser de valor monetário implementado em W2-F9

---

## Decisões de Baixa Reversibilidade

| Decisão | Justificativa | Reversibilidade |
|---------|---------------|-----------------|
| **Endpoint `/historico/exportar` (CSV)** | Novo endpoint na API. Remover não quebra o frontend (botão pode ser desabilitado), mas introduz contrato permanente. | Baixa — requer depreciação do endpoint se removido |
| **Parser de valor monetário no frontend** | Lógica de parsing "R$ 10.000,00" → número centralizada em util. Mudar formato requer atualização em múltiplos lugares. | Média — extrair para `lib/formatters.ts` mitiga |

---

## Riscos e Pontos de Atenção

1. **Status de emissão:** O TODO menciona `erro_emissao` mas o banco e emissor usam `erro`. O frontend deve usar `erro`. Se futuramente houver um `erro_emissao` específico, o polling já está preparado.

2. **Polling excessivo:** Polling a cada 5s pode gerar carga se muitos operadores aprovarem simultaneamente. O intervalo deve ser cancelado (`clearInterval`) ao desmontar o componente e quando status mudar.

3. **Filtros client-side no histórico:** Se o histórico crescer além de ~500 registros, a paginação server-side existente (`limit/offset`) precisa ser combinada com filtros server-side para não paginar dados filtrados incorretamente. **Mitigação:** implementar filtros client-side sobre a página atual, não sobre todo o dataset.

4. **CORS em link para PJE:** O link externo para `pje.tjdft.jus.br` pode ser bloqueado por CSP. Verificar `Content-Security-Policy` do nginx.

5. **PDF de demonstrativo:** A URL `/dados/demonstrativos/` pode não estar exposta pelo nginx. Confirmar mapeamento de volumes antes de implementar W3-F10.

---

## Critérios de Aceite por Wave

### Wave 1 — Aceite
- [ ] Todas as 5 features funcionam em ambiente de desenvolvimento
- [ ] Testes unitários cobrem todos os componentes novos (meta: 60%+)
- [ ] Nenhum teste existente quebra (36/36 passando)
- [ ] Filtro de busca responde em < 100ms para fila com 50 processos

### Wave 2 — Aceite
- [ ] Todas as 4 features funcionam em ambiente de desenvolvimento
- [ ] Polling de emissão para corretamente quando processo muda de status
- [ ] Aviso de valor alto dispara apenas para valores > R$ 50.000
- [ ] Documentos e compensação renderizam com dados reais da API

### Wave 3 — Aceite
- [ ] Todas as 5 features funcionam em ambiente de desenvolvimento
- [ ] Paginação carrega próxima página em < 500ms
- [ ] Exportação CSV gera arquivo válido com acentuação correta
- [ ] Prioridade na fila reflete regras de negócio definidas
- [ ] Cobertura de testes mantida acima de 60%

---

## Checklist de Entrega Final

- [ ] Plano técnico revisado e salvo em `.kimi/plans/todo-frontend.md`
- [ ] Cada feature mapeada para wave específica
- [ ] Critérios de aceite mensuráveis por wave
- [ ] Nenhuma reescrita completa de módulos
- [ ] Abordagens preferencialmente reversíveis
- [ ] Endpoint novo sinalizado explicitamente (W3-F14)
- [ ] MEMORY.md atualizado com decisões arquiteturais
