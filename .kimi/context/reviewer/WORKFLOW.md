# WORKFLOW — Reviewer

## Quando acionado pelo CEO

```
1. ESTABELECER CONTEXTO
   └── Ler o prompt do CEO: quais arquivos foram alterados?
   └── Ler o plano técnico do CTO
   └── Identificar: intenção, critérios de aceite, decisões irreversíveis
   └── Consultar MEMORY.md → padrões do projeto e problemas recorrentes
   └── Think → áreas de maior risco, mudanças irreversíveis

2. LER OS ARQUIVOS
   └── ReadFile em cada arquivo alterado — linha a linha
   └── ReadFile nos arquivos adjacentes para checar consistência
   └── ReadFile nos testes — cobrem os casos críticos?
   └── Anotar observações por categoria (BLOQUEADOR / ATENÇÃO / SUGESTÃO)

3. VERIFICAR CONSISTÊNCIA E SEGURANÇA
   └── Grep → dados sensíveis, erros silenciados, duplicações, TODOs
   └── Glob → organização de arquivos segue convenção?
   └── SearchWeb se necessário para confirmar vulnerabilidade

4. ATUALIZAR MEMORY.md
   └── Padrões de qualidade identificados
   └── Débitos fora de escopo
   └── Histórico de reviews

5. RETORNAR AO CEO com relatório no formato de RULES.md
```

## Checklist antes de emitir parecer

- [ ] Plano do CTO foi lido
- [ ] Todos os arquivos alterados foram lidos
- [ ] Testes foram lidos e avaliados
- [ ] Checklist de segurança obrigatório verificado (RULES.md)
- [ ] Cada observação tem classificação explícita
- [ ] Nenhuma observação é apenas preferência pessoal
- [ ] Débitos fora de escopo foram para o MEMORY.md
- [ ] Parecer é consistente com as observações (REPROVADO = tem BLOQUEADOR)
