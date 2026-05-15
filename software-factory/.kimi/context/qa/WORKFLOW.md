# WORKFLOW — QA

## Quando acionado pelo CEO

```
1. EXTRAIR CRITÉRIOS DE ACEITE
   └── Ler o prompt do CEO com atenção
   └── Identificar todos os critérios de aceite explícitos
   └── Inferir critérios implícitos (ex: se "criar usuário" → GET depois
       deve retornar o usuário criado)
   └── Usar Think para planejar os casos de teste

2. MAPEAR O QUE FOI IMPLEMENTADO
   └── ReadFile nos arquivos listados pelo dev_senior
   └── Glob para verificar se há arquivos alterados não mencionados
   └── Ler os testes existentes (o que já está coberto?)
   └── Consultar MEMORY.md → configuração do ambiente de testes

3. EXECUTAR TESTES AUTOMATIZADOS
   └── Shell: rodar a suite completa de testes
   └── Shell: rodar apenas os testes dos módulos alterados
   └── Registrar output completo (não apenas o resumo final)

4. TESTAR MANUALMENTE CASOS CRÍTICOS
   └── Happy path (fluxo principal com input válido)
   └── Input inválido (null, vazio, tipo errado, valor extremo)
   └── Fluxo de erro (o que retorna quando algo falha?)
   └── Casos de borda específicos do domínio

5. VERIFICAR EFEITOS COLATERAIS
   └── O que mudou nos módulos vizinhos?
   └── Há algo que antes funcionava que pode ter quebrado?
   └── Grep: funções alteradas → onde são usadas?

6. ATUALIZAR MEMORY.md
   └── Registrar padrões de bugs novos encontrados
   └── Atualizar configuração de ambiente se necessário
   └── Registrar no histórico de validações

7. RETORNAR AO CEO
   └── Relatório completo no formato definido em RULES.md
   └── Parecer final: APROVADO ou REPROVADO
   └── Se REPROVADO: bugs ordenados por severidade
```

---

## Checklist de validação mínima

Para qualquer feature, verificar:

- [ ] Testes automatizados passam sem warnings
- [ ] Happy path funciona conforme especificado
- [ ] Input inválido retorna erro adequado (não 500)
- [ ] Campos obrigatórios ausentes são rejeitados
- [ ] Autenticação/autorização é verificada (se aplicável)
- [ ] Operações destrutivas (DELETE, UPDATE) têm verificação de ownership
- [ ] Não há dados sensíveis expostos em responses ou logs
- [ ] Todos os critérios de aceite do plano foram verificados
