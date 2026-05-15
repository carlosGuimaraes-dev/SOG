# TOOLS — Docs Writer

## Ferramentas disponíveis e quando usar

---

### `Think`
Use antes de começar a redigir. Decida:
- Quem é o leitor desta documentação?
- Qual é o formato mais adequado? (README, docstring, changelog, guia, ADR)
- Qual nível de detalhe é necessário?
- O que o leitor precisa saber ANTES de ler este documento?

---

### `ReadFile`
Sua ferramenta principal. Leia sempre:
- O código implementado (fonte da verdade — não confie no plano, confie no código)
- Documentação existente (para manter consistência de formato e tom)
- Testes (revelam comportamentos esperados que a doc precisa cobrir)
- Arquivos de configuração (versões, variáveis de ambiente, dependências)

**Regra de ouro**: a documentação descreve o que o código FAZ, não o que
deveria fazer. Leia o código antes de escrever uma linha.

---

### `Glob`
Use para mapear o projeto antes de escrever documentação de alto nível
(README, guia de contribuição, visão geral de arquitetura).

```
Glob: src/**/*.py     → mapear módulos existentes
Glob: docs/**/*.md    → encontrar documentação existente
Glob: **/*.env*       → encontrar variáveis de ambiente
```

---

### `Grep`
Use para encontrar todos os usos de uma função/endpoint/variável antes
de documentá-los — garante que você cobre todos os contextos relevantes.

```
Grep: "def "          → listar todas as funções públicas de um módulo
Grep: "@router\."     → listar todos os endpoints de um router FastAPI
Grep: "process\.env"  → listar todas as variáveis de ambiente usadas
```

---

### `WriteFile`
Use para criar os documentos finais. Sempre escreva o arquivo completo.
Salve na localização correta conforme o tipo:

| Tipo de doc          | Localização padrão              |
|----------------------|---------------------------------|
| README principal     | `README.md`                     |
| Guia de instalação   | `docs/setup.md`                 |
| Referência de API    | `docs/api.md`                   |
| Changelog            | `CHANGELOG.md`                  |
| ADR (decisão)        | `docs/adr/NNN-titulo.md`        |
| Docstrings           | No próprio arquivo de código    |
| Guia de contribuição | `CONTRIBUTING.md`               |

---

### `StrReplaceFile`
Use para atualizar documentação existente — adicionar seção de changelog,
atualizar versão no README, corrigir exemplo desatualizado.

---

### `SearchWeb` / `FetchURL`
Use para consultar:
- Convenções de formato (ex: Keep a Changelog, Conventional Commits)
- Padrões de documentação de APIs (OpenAPI, JSDoc, etc.)
- Verificar se uma lib referenciada tem docs oficiais para linkar
