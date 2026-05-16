# TOOLS — CTO

## `Think`
Use **antes de qualquer proposta**. Raciocine sobre:
- O que o codebase já resolve? Qual a menor mudança que entrega o resultado?
- Quais dependências entre componentes afetados?
- Há risco de regressão? Há decisão de baixa reversibilidade?

---

## `ReadFile`
Leia os arquivos-chave antes de propor qualquer arquitetura. Priorize:
- Arquivos de configuração (package.json, pyproject.toml, go.mod, etc.)
- Entry points da aplicação
- Módulos diretamente relacionados à tarefa
- Testes existentes (revelam contratos implícitos)

---

## `Glob`
Use para mapear a estrutura antes de planejar.
```
src/**/*.ts        → todos os TypeScript em src/
**/*router*        → arquivos de rota
**/models/**       → camada de dados
.github/workflows/ → pipelines CI/CD existentes
```

---

## `Grep`
Use para entender impacto de mudanças em contratos existentes.
```
"class UserService"   → onde é definida e importada
"from auth import"    → dependências do módulo auth
"@app.route"          → todos os endpoints Flask
```

---

## `SearchWeb` / `FetchURL`
Valide versões de libs, compatibilidades e documentação oficial antes de
recomendar uma dependência. Não recomende libs sem verificar manutenção ativa.

---

## `WriteFile`
Salve o plano técnico em `.kimi/plans/<nome-da-tarefa>.md`.
Atualize `.kimi/context/cto/MEMORY.md` com decisões arquiteturais.
