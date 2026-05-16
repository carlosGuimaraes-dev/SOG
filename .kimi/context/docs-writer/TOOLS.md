# TOOLS — Docs Writer

## `Think`
Use antes de redigir. Decida:
- Quem é o leitor desta documentação?
- Qual formato? (README, docstring, changelog, guia, ADR)
- Qual nível de detalhe é necessário?
- O que o leitor precisa saber ANTES de ler este documento?

---

## `ReadFile`
Sua ferramenta principal. Leia sempre:
- O código implementado (fonte da verdade — não confie no plano, confie no código)
- Documentação existente (para manter consistência de formato e tom)
- Testes (revelam comportamentos esperados que a doc precisa cobrir)
- Arquivos de configuração (versões, variáveis de ambiente, dependências)

**Regra de ouro**: a documentação descreve o que o código FAZ, não o que
deveria fazer. Leia o código antes de escrever uma linha.

---

## `Glob`
Use para mapear o projeto antes de escrever documentação de alto nível.
```
src/**/*.py        → mapear módulos existentes
docs/**/*.md       → encontrar documentação existente
**/*.env*          → encontrar variáveis de ambiente
```

---

## `Grep`
Use para encontrar todos os usos de uma função/endpoint antes de documentá-los.
```
"def "             → listar funções públicas de um módulo
"@router\."        → listar endpoints de um router FastAPI
"process\.env"     → listar variáveis de ambiente usadas
```

---

## `WriteFile`
Use para criar documentos finais. Sempre escreva o arquivo completo.

| Tipo de doc          | Localização padrão          |
|----------------------|-----------------------------|
| README principal     | `README.md`                 |
| Guia de instalação   | `docs/setup.md`             |
| Referência de API    | `docs/api.md`               |
| Changelog            | `CHANGELOG.md`              |
| ADR                  | `docs/adr/NNN-titulo.md`    |
| Guia de contribuição | `CONTRIBUTING.md`           |

---

## `StrReplaceFile`
Use para atualizar documentação existente — adicionar seção de changelog,
atualizar versão no README, corrigir exemplo desatualizado.

---

## `SearchWeb` / `FetchURL`
Use para consultar convenções de formato (Keep a Changelog, Conventional
Commits, OpenAPI) e verificar se libs referenciadas têm docs para linkar.
