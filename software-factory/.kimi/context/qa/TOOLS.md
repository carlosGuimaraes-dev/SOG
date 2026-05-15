# TOOLS — QA

## Ferramentas disponíveis e quando usar

---

### `Think`
Use antes de começar a validar. Planeje:
- Quais são os critérios de aceite? (leia do prompt do CEO)
- Quais são os casos felizes (happy path)?
- Quais são os casos de borda?
- Quais são os casos de erro esperados?
- O que pode ter efeito colateral nos módulos vizinhos?

---

### `Shell`
Sua ferramenta principal de validação. Use para:

**Rodar a suite de testes:**
```bash
pytest tests/ -v                    # Python
npm test                            # Node
go test ./...                       # Go
```

**Rodar testes específicos:**
```bash
pytest tests/test_auth.py -v -k "test_login"
```

**Verificar cobertura:**
```bash
pytest --cov=src tests/
```

**Testar endpoints HTTP (se aplicável):**
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

**Sempre leia o output completo.** Não assuma que passou.

---

### `ReadFile`
Use para:
- Ler os arquivos implementados e entender o comportamento esperado
- Ler os testes existentes para entender o que já está coberto
- Verificar o tratamento de erros (o que o código faz em casos de exceção)

---

### `Grep`
Use para:
- Encontrar todos os pontos de entrada do código validado
- Verificar se há tratamento de erro em todos os fluxos
- Encontrar chamadas a serviços externos que precisam de mock nos testes

```
Grep: "except\|catch\|error"  → verificar tratamento de erros
Grep: "TODO\|FIXME\|HACK"     → encontrar código incompleto
```

---

### `Glob`
Use para mapear os arquivos alterados e garantir que validou
todos eles — não apenas os mencionados pelo dev_senior.
