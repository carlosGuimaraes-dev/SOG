# TODO — Melhorias do Dashboard

> Priorizado em 3 ondas. Executar amanhã.

---

## 🔴 Onda 1 — Essencial para operar (bloqueante)

- [ ] **Exibir logs de execução no detalhe do processo**
  - Mostrar `logs` retornados pela API (`/processos/{id}`)
  - Timeline com etapa, status (ok/erro/aviso), mensagem e timestamp
  - Destacar erros em vermelho

- [ ] **Exibir tentativas e erro_msg**
  - Mostrar campo `tentativas` no card do processo
  - Se `erro_msg` estiver preenchido, exibir alerta visível
  - Status `erro` deve aparecer na fila com destaque

- [ ] **Criar "Resumo do Preenchimento Automático"**
  - Card compacto no topo do detalhe com:
    - Sucumbente selecionado
    - Peças marcadas (contagem por tipo)
    - Itens da guia incluídos
    - Valor total calculado
  - Isso evita que o operador tenha que decifrar os dados brutos

- [ ] **Busca por número de processo na fila**
  - Input de busca no topo da Fila
  - Filtrar em tempo real (client-side) ou via API

- [ ] **Link direto para o PJE**
  - No detalhe do processo, botão "Abrir no PJE" com URL montada
  - `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso={numero}`

---

## 🟡 Onda 2 — Confiança na aprovação

- [ ] **Exibir documentos PJE extraídos**
  - Lista de documentos retornada pela API
  - Mostrar tipo, data de assinatura, nome

- [ ] **Exibir dados de compensação**
  - Campo `compensacao` do banco (JSON array)
  - Tabela com data, valor, guia de origem

- [ ] **Status da emissão com polling**
  - Após aprovar, mostrar spinner "Emissão em andamento..."
  - Polling a cada 5s na API para verificar status
  - Estados: `aprovado` → `emitido` | `erro_emissao`
  - Toast de sucesso quando concluir

- [ ] **Melhorar avisos/alertas no detalhe**
  - Destacar visualmente quando:
    - Área não mapeada (outros itens precisam conferência)
    - Suspensão de exigibilidade detectada
    - Sucumbente não identificado
    - Valor muito alto (threshold configurável)

---

## 🟢 Onda 3 — Produtividade

- [ ] **Preview/link do PDF do demonstrativo**
  - Link para abrir o PDF gerado em `/dados/demonstrativos/`
  - Ou iframe/embed se possível

- [ ] **Paginação no histórico**
  - Usar `limit/offset` da API
  - Botões "Anterior / Próximo" ou numeração de páginas

- [ ] **Filtros no histórico**
  - Por status (emitido / rejeitado)
  - Por data (últimos 7 dias, 30 dias, etc.)
  - Por valor (maior que X)

- [ ] **Indicadores de prioridade na fila**
  - Processos mais antigos = maior prioridade (cor diferente)
  - Valor acima de threshold = destaque
  - Badge de urgência para processos com erro nas tentativas

- [ ] **Exportação do histórico**
  - Botão "Exportar CSV" ou "Exportar Excel"
  - Endpoint na API para download

---

## 📌 Notas

- Commitar cada item separadamente
- Manter testes passando (36/36)
- Atualizar README conforme novas features são adicionadas
