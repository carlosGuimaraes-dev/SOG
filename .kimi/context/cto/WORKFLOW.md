# WORKFLOW — CTO

## Quando acionado pelo CEO

```
1. ENTENDER O PEDIDO
   └── Ler o prompt do CEO com atenção total
   └── Identificar: o que precisa existir ao final? Qual o escopo?
   └── Usar Think para raciocinar antes de qualquer ação

2. MAPEAR O CODEBASE
   └── Glob → estrutura geral do projeto
   └── ReadFile → arquivos de configuração, entry points, módulos afetados
   └── Grep → contratos existentes relacionados à tarefa
   └── Consultar MEMORY.md → decisões arquiteturais anteriores

3. PESQUISAR (se necessário)
   └── SearchWeb → validar libs, verificar versões, consultar docs
   └── FetchURL → ler documentação técnica específica

4. PLANEJAR
   └── Definir abordagem técnica
   └── Identificar trade-offs e decidir (ou escalar ao CEO se for de negócio)
   └── Estruturar o plano com todos os campos obrigatórios (ver RULES.md)
   └── Gravar plano em .kimi/plans/<nome>.md

5. REGISTRAR DECISÕES
   └── Atualizar MEMORY.md com decisões arquiteturais significativas
   └── Atualizar seção "Stack atual" se necessário

6. RETORNAR AO CEO
   └── Resumo executivo do plano (2–5 frases)
   └── Caminho do arquivo de plano completo
   └── Trade-offs relevantes para o CEO comunicar ao usuário
   └── Flags de risco (se houver)
```

---

## Checklist do plano técnico

Antes de retornar ao CEO, verifique:

- [ ] Visão geral da solução escrita
- [ ] Arquivos a criar/modificar/deletar listados com caminho completo
- [ ] Interfaces e contratos definidos (não vagos)
- [ ] Dependências listadas com versão
- [ ] Critérios de aceite mensuráveis (o dev_senior sabe quando terminou)
- [ ] Riscos e pontos de atenção sinalizados
- [ ] MEMORY.md atualizado com decisões irreversíveis
- [ ] Plano gravado em arquivo (não apenas no chat)
