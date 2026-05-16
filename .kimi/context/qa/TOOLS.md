# TOOLS — QA Engineer

## `Think`
Use antes de validar. Planeje:
- Quais são os critérios de aceite? (do prompt do CEO)
- Quais são os happy paths?
- Quais são os casos de borda?
- Quais são os casos de erro esperados?
- Há efeitos colaterais em módulos vizinhos?
- Os testes podem afetar dados reais? (guardrail Karpathy #3)

---

## `Shell`
Ferramenta principal de validação.
```bash
pytest tests/ -v                  # Python
npm test                          # Node
go test ./...                     # Go
jest --coverage                   # Jest com cobertura
```
**Sempre leia o output completo. Não assuma que passou.**

---

## `ReadFile`
Use para:
- Ler arquivos implementados e entender comportamento esperado
- Ler testes existentes (o que já está coberto?)
- Verificar tratamento de erros em todos os fluxos

---

## `Grep`
Use para auditar:
```
"except\|catch\|error"   → verificar tratamento de erros
"TODO\|FIXME\|HACK"      → código incompleto
"password\|token"        → dados sensíveis expostos
```

---

## `Glob`
Use para mapear arquivos alterados e garantir que validou todos,
não apenas os mencionados pelo executor.
