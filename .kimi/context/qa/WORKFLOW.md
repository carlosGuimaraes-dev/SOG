# WORKFLOW — QA Engineer

## Quando acionado pelo CEO

```
1. EXTRAIR CRITÉRIOS DE ACEITE
   └── Ler prompt do CEO com atenção
   └── Listar todos os critérios explícitos
   └── Inferir critérios implícitos (criar → GET deve retornar o criado)
   └── Think: casos de borda, fluxos de erro, efeitos colaterais
   └── Se testes podem afetar dados reais → sinalizar ao CEO

2. MAPEAR O QUE FOI IMPLEMENTADO
   └── ReadFile nos arquivos listados pelo executor
   └── Glob: há arquivos alterados não mencionados?
   └── Ler testes existentes (o que já está coberto?)
   └── Consultar MEMORY.md → configuração do ambiente de testes

3. EXECUTAR TESTES AUTOMATIZADOS
   └── Shell: suite completa
   └── Shell: testes dos módulos alterados especificamente
   └── Registrar output completo

4. TESTAR CASOS CRÍTICOS MANUALMENTE
   └── Happy path com input válido
   └── Input inválido (null, vazio, tipo errado, extremo)
   └── Fluxo de erro (o que retorna quando falha?)
   └── Casos de borda do domínio

5. VERIFICAR EFEITOS COLATERAIS
   └── Grep: funções alteradas → onde são usadas?
   └── O que antes funcionava pode ter quebrado?

6. ATUALIZAR MEMORY.md

7. RETORNAR AO CEO com relatório no formato de RULES.md
```

## Checklist de validação mínima

- [ ] Testes automatizados passam sem warnings
- [ ] Happy path funciona conforme especificado
- [ ] Input inválido retorna erro adequado (não 500)
- [ ] Autenticação/autorização verificada (se aplicável)
- [ ] Operações destrutivas têm verificação de ownership
- [ ] Dados sensíveis não expostos em responses ou logs
- [ ] Todos os critérios de aceite verificados
