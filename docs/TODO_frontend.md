# TODO — Melhorias do Dashboard

> Priorizado em 3 ondas. Executar amanhã.

---

## 🔴 Onda 1 — Essencial para operar (bloqueante)

> **Implementado em 2026-05-15** — QA aprovado (41/41 testes), Reviewer aprovado.

- [x] **Exibir logs de execução no detalhe do processo**
  - Mostrar `logs` retornados pela API (`/processos/{id}`)
  - Timeline com etapa, status (ok/erro/aviso), mensagem e timestamp
  - Destacar erros em vermelho

- [x] **Exibir tentativas e erro_msg**
  - Mostrar campo `tentativas` no card do processo
  - Se `erro_msg` estiver preenchido, exibir alerta visível
  - Status `erro` deve aparecer na fila com destaque

- [x] **Criar "Resumo do Preenchimento Automático"**
  - Card compacto no topo do detalhe com:
    - Sucumbente selecionado
    - Peças marcadas (contagem por tipo)
    - Itens da guia incluídos
    - Valor total calculado
  - Isso evita que o operador tenha que decifrar os dados brutos

- [x] **Busca por número de processo na fila**
  - Input de busca no topo da Fila
  - Filtrar em tempo real (client-side) ou via API

- [x] **Link direto para o PJE**
  - No detalhe do processo, botão "Abrir no PJE" com URL montada
  - `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso={numero}`

---

## 🟡 Onda 2 — Confiança na aprovação

- [x] **Exibir documentos PJE extraídos**
  - Lista de documentos retornada pela API
  - Mostrar tipo, data de assinatura, nome

- [x] **Exibir dados de compensação**
  - Campo `compensacao` do banco (JSON array)
  - Tabela com data, valor, guia de origem

- [x] **Status da emissão com polling**
  - Após aprovar, mostrar spinner "Emissão em andamento..."
  - Polling a cada 5s na API para verificar status
  - Estados: `aprovado` → `emitido` | `erro_emissao`
  - Toast de sucesso quando concluir

- [x] **Melhorar avisos/alertas no detalhe**
  - Destacar visualmente quando:
    - Área não mapeada (outros itens precisam conferência)
    - Suspensão de exigibilidade detectada
    - Sucumbente não identificado
    - Valor muito alto (threshold configurável)

---

## 🟢 Onda 3 — Produtividade

- [x] **Preview/link do PDF do demonstrativo**
  - Link para abrir o PDF gerado em `/dados/demonstrativos/`
  - Verificação de disponibilidade via HEAD request

- [x] **Paginação no histórico**
  - Client-side, 20 registros/página
  - Botões "Anterior / Próximo"

- [x] **Filtros no histórico**
  - Por status (emitido / rejeitado)
  - Por data (últimos 7, 30, 90 dias)
  - Por valor mínimo

- [x] **Indicadores de prioridade na fila**
  - Processos mais antigos (> 7 dias) = badge cinza
  - Valor acima de threshold (> R$ 50k) = badge amarelo
  - Badge de urgência para processos com erro nas tentativas = badge vermelho

- [x] **Exportação do histórico**
  - Botão "Exportar CSV"
  - Download via `api.get(blob)` com refresh token automático
  - Rate limit do endpoint: `10/minute`

---

## 📌 Notas

- Commitar cada item separadamente
- Manter testes passando
- Atualizar README conforme novas features são adicionadas

> **Implementação Wave 2 (2026-05-15):** 4/4 features entregues. QA aprovado (86/86 testes). Reviewer aprovou com ressalvas não-bloqueantes (registradas em `.kimi/context/frontend/MEMORY.md`).

> **Implementação Wave 3 (2026-05-15):** 5/5 features entregues. QA aprovado (124/124 testes). Reviewer aprovou (ressalvas corrigidas: botão exportar usa `api.get(blob)`; rate limit reduzido para `10/minute`).

> **🏁 Projeto Frontend concluído.** Todas as ondas (1, 2 e 3) implementadas, testadas e aprovadas.
