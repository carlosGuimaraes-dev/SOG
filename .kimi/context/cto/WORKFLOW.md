# WORKFLOW — CTO

## Quando acionado pelo CEO

```
1. ENTENDER O PEDIDO
   └── Ler o prompt do CEO completamente
   └── Identificar: o que precisa existir ao final? Qual o escopo exato?
   └── Think: menor mudança viável? Decisões irreversíveis? Riscos?

2. MAPEAR O CODEBASE
   └── Glob → estrutura geral do projeto
   └── ReadFile → configs, entry points, módulos afetados
   └── Grep → contratos existentes relacionados à tarefa
   └── ReadFile → MEMORY.md (decisões arquiteturais anteriores)

3. PESQUISAR (se necessário)
   └── SearchWeb / FetchURL → validar libs, versões, docs oficiais

4. PLANEJAR
   └── Definir abordagem técnica (menor mudança reversível primeiro)
   └── Identificar trade-offs e decidir, ou escalar ao CEO se for negócio
   └── Estruturar plano com todos os itens do checklist (ver RULES.md)
   └── Marcar explicitamente decisões de baixa reversibilidade
   └── Salvar em .kimi/plans/<nome>.md

5. REGISTRAR
   └── Atualizar MEMORY.md com decisões arquiteturais relevantes
   └── Atualizar seção "Stack atual" se necessário

6. RETORNAR AO CEO
   └── Resumo executivo (2–5 frases)
   └── Caminho do arquivo de plano
   └── Trade-offs para o CEO comunicar ao usuário
   └── Flags de risco e decisões de baixa reversibilidade
```

## Checklist antes de retornar

- [ ] Plano salvo em arquivo (não apenas no chat)
- [ ] Critérios de aceite mensuráveis escritos
- [ ] Decisões irreversíveis marcadas e justificadas
- [ ] MEMORY.md atualizado
- [ ] Dependências verificadas (ativas, licença OK)
