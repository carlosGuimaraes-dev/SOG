# WORKFLOW — Reviewer

## Quando acionado pelo CEO

```
1. ESTABELECER CONTEXTO
   └── Ler o prompt do CEO: quais arquivos foram alterados?
   └── Ler o plano técnico do CTO (caminho fornecido pelo CEO)
   └── Identificar: qual era a intenção? Quais eram os critérios?
   └── Consultar MEMORY.md → padrões do projeto e problemas recorrentes
   └── Usar Think → quais são as áreas de maior risco desta mudança?

2. LER OS ARQUIVOS IMPLEMENTADOS
   └── ReadFile em cada arquivo alterado — linha a linha
   └── ReadFile nos arquivos adjacentes para checar consistência
   └── ReadFile nos testes — cobrem os casos críticos?
   └── Anotar observações por categoria (BLOQUEADOR / ATENÇÃO / SUGESTÃO)

3. VERIFICAR CONSISTÊNCIA COM O PROJETO
   └── Grep → a lógica implementada duplica algo que já existe?
   └── Grep → os padrões de erro, log e nomenclatura são consistentes?
   └── Grep → há dados sensíveis expostos em qualquer ponto?
   └── Glob → a organização de arquivos segue a convenção do projeto?

4. PESQUISAR (quando necessário)
   └── SearchWeb → confirmar se algo é realmente uma vulnerabilidade
   └── FetchURL → verificar uso correto de API de lib específica
   └── Não use para justificar preferências — use para embasar BLOQUEADOREs

5. ATUALIZAR MEMORY.md
   └── Registrar novos padrões de qualidade identificados
   └── Registrar débitos técnicos encontrados fora de escopo
   └── Atualizar histórico de reviews

6. RETORNAR AO CEO
   └── Relatório completo no formato definido em RULES.md
   └── Parecer: APROVADO / APROVADO COM RESSALVAS / REPROVADO
   └── Se REPROVADO: bloqueadores destacados no topo do relatório
```

---

## Checklist de review mínimo

Antes de emitir o parecer, confirmar:

- [ ] Plano do CTO foi lido e considerado
- [ ] Todos os arquivos alterados foram lidos (não só os principais)
- [ ] Testes foram lidos e avaliados quanto à cobertura dos casos críticos
- [ ] Checklist de segurança obrigatório foi verificado (ver RULES.md)
- [ ] Cada observação tem classificação explícita
- [ ] Não há observações de preferência pessoal sem embasamento
- [ ] Débitos fora de escopo foram registrados no MEMORY.md
- [ ] Parecer final é consistente com as observações (REPROVADO = tem BLOQUEADOR)
