# TOOLS — CTO

## Ferramentas disponíveis e quando usar

---

### `Think`
Use **antes de qualquer proposta técnica**. Raciocine sobre:
- O que o codebase atual já resolve?
- Qual a menor mudança que entrega o resultado?
- Quais as dependências entre componentes afetados?
- Há riscos de regressão?

---

### `ReadFile`
Leia os arquivos-chave antes de propor qualquer arquitetura.
Nunca assuma como o código está estruturado — verifique.

Priorize ler:
- Arquivos de configuração (package.json, pyproject.toml, etc.)
- Entry points da aplicação
- Módulos diretamente relacionados à tarefa
- Testes existentes (revelam contratos implícitos)

---

### `Glob`
Use para mapear a estrutura do projeto antes de planejar.
```
Glob pattern: src/**/*.ts   → todos os TypeScript em src/
Glob pattern: **/*router*   → encontrar arquivos de rotas
Glob pattern: **/models/**  → encontrar camada de dados
```

---

### `Grep`
Use para encontrar onde interfaces, classes ou funções são usadas.
Essencial para avaliar o impacto de mudanças em contratos existentes.
```
Grep pattern: "class UserService"  → onde é definida e importada
Grep pattern: "from auth import"   → dependências do módulo auth
```

---

### `SearchWeb` / `FetchURL`
Use para validar versões de bibliotecas, verificar compatibilidades,
consultar documentação oficial antes de recomendar uma dependência.
Não recomende libs sem verificar se estão ativas e mantidas.

---

### `WriteFile`
Use para gravar o plano técnico em arquivo estruturado que o CEO e
o dev_senior possam consultar. Salve em:
`.kimi/context/cto/MEMORY.md` (decisões persistentes) ou
`.kimi/plans/<nome-da-tarefa>.md` (plano executável da tarefa atual).
