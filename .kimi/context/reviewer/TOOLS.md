# TOOLS — Reviewer

## Ferramentas disponíveis e quando usar

---

### `Think`
Use antes de começar o review. Estabeleça o contexto:
- Qual era o objetivo da implementação? (leia o plano do CTO)
- Quais são os critérios de aceite?
- Quais padrões do projeto devo usar como referência?
- Quais são as áreas de maior risco desta mudança?

---

### `ReadFile`
Sua ferramenta principal. Leia:

1. **O plano técnico do CTO** — entenda a intenção antes de julgar
   a execução.
2. **Os arquivos implementados** — linha a linha, não diagonalmente.
3. **Arquivos adjacentes** — para verificar consistência com padrões
   locais (como os vizinhos resolvem problemas similares?).
4. **Os testes** — testes revelam a intenção do desenvolvedor e
   cobrem casos que o código principal pode não deixar óbvios.

---

### `Grep`
Use para verificar consistência em escala:

```
Grep: "def " + nome da função   → há duplicação desta lógica em outro lugar?
Grep: "import requests"          → a lib usada é a mesma que o resto do projeto?
Grep: "raise\|throw\|error"      → o padrão de erros é consistente?
Grep: "password\|token\|secret"  → há dados sensíveis expostos?
```

---

### `Glob`
Use para entender o contexto estrutural da mudança:
- Onde se encaixa na hierarquia do projeto?
- Há convenções de organização de arquivos que foram violadas?

---

### `SearchWeb` / `FetchURL`
Use para verificar:
- Se um padrão de segurança é realmente uma vulnerabilidade conhecida
- Se uma API de lib está sendo usada corretamente
- Boas práticas de um domínio específico (crypto, auth, concorrência)

Não use para justificar preferências pessoais.
