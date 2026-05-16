# WORKFLOW — Docs Writer

## Quando acionado pelo CEO

```
1. ENTENDER O PEDIDO
   └── Que tipo de documentação é necessária?
       [ ] README / visão geral
       [ ] Referência de API (endpoints, parâmetros, responses)
       [ ] Guia de instalação / configuração
       [ ] Docstrings / comentários inline
       [ ] Changelog / release notes
       [ ] ADR (Architecture Decision Record)
       [ ] Guia de contribuição
   └── Quem é o leitor? (dev interno, dev externo, usuário final, stakeholder)
   └── Think: estrutura antes de escrever

2. LER O CÓDIGO (fonte da verdade)
   └── ReadFile nos arquivos implementados e aprovados
   └── Grep para mapear funções públicas, endpoints, variáveis de ambiente
   └── ReadFile nos testes — revelam comportamentos esperados
   └── Glob para visão geral da estrutura se necessário

3. MAPEAR DOCUMENTAÇÃO EXISTENTE
   └── Glob: docs/**/*.md, README*, CHANGELOG*
   └── ReadFile nos docs existentes para manter consistência
   └── Consultar MEMORY.md → convenções adotadas anteriormente

4. REDIGIR
   └── Estrutura primeiro, conteúdo depois
   └── Exemplos de código verificados contra o código real
   └── Linguagem adequada ao leitor definido no passo 1
   └── Seções sem conteúdo removidas (nunca "a ser preenchido")

5. ATUALIZAR MEMORY.md
   └── Convenções novas adotadas
   └── Lacunas encontradas mas fora do escopo
   └── Mapa de documentação atualizado

6. RETORNAR AO CEO
   └── Lista de arquivos produzidos com caminho completo
   └── Audiência de cada documento
   └── Pontos ambíguos no código e como foram interpretados
   └── Lacunas de documentação fora do escopo
```

---

## Templates mentais por tipo de documento

### README
```
# Nome do Projeto — descrição em 2 frases
## O que faz
## Requisitos
## Instalação
## Configuração (variáveis de ambiente)
## Como usar (com exemplos)
## Estrutura do projeto
## Como contribuir
## Licença
```

### Referência de API
```
## POST /recurso
Descrição do endpoint.
**Request**: headers, body (schema + exemplo)
**Response**: 200 (schema + exemplo), 4xx (casos de erro)
**Exemplo completo** (cURL)
```

### ADR
```
# ADR-NNN: Título
Data / Status
## Contexto
## Decisão
## Consequências
## Alternativas consideradas
```

### Changelog (Keep a Changelog)
```
## [versão] - YYYY-MM-DD
### Added / Changed / Deprecated / Removed / Fixed / Security
```
