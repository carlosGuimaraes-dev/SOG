# TOOLS — Reviewer

## `Think`
Use antes de começar. Estabeleça o contexto:
- Qual era a intenção do plano do CTO?
- Quais são os critérios de aceite?
- Quais são as áreas de maior risco desta mudança?
- Há decisões de baixa reversibilidade? (guardrail Karpathy #3)

---

## `ReadFile`
Sua ferramenta principal. Leia:
1. O plano técnico do CTO — entenda a intenção antes de julgar a execução
2. Os arquivos implementados — linha a linha
3. Arquivos adjacentes — para verificar consistência com padrões locais
4. Os testes — cobrem os casos críticos?

---

## `Grep`
Use para verificar consistência em escala:
```
"password\|token\|secret"     → dados sensíveis expostos?
"except:\|catch {}"           → erros silenciados?
"import <modulo>"             → duplicação de lógica existente?
"TODO\|FIXME"                 → código incompleto não sinalizado?
```

---

## `Glob`
Use para entender se a organização de arquivos segue as convenções
do projeto e se há arquivos alterados fora do escopo declarado.

---

## `SearchWeb` / `FetchURL`
Use para confirmar se algo é realmente uma vulnerabilidade conhecida
ou para verificar uso correto de API de lib específica.
Não use para justificar preferências pessoais.
