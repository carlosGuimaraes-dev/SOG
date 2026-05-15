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
   └── Usar Think para definir estrutura antes de escrever

2. LER O CÓDIGO (fonte da verdade)
   └── ReadFile nos arquivos implementados
   └── Grep para mapear funções públicas, endpoints, variáveis de ambiente
   └── ReadFile nos testes — revelam comportamentos esperados
   └── Glob para ter visão geral da estrutura se necessário

3. MAPEAR DOCUMENTAÇÃO EXISTENTE
   └── Glob: docs/**/*.md, README*, CHANGELOG*
   └── ReadFile nos docs existentes para manter consistência de tom e formato
   └── Consultar MEMORY.md → convenções adotadas anteriormente

4. REDIGIR
   └── Estrutura primeiro, conteúdo depois
   └── Exemplos de código sempre verificados contra o código real
   └── Linguagem adequada ao leitor definido no passo 1

5. ATUALIZAR MEMORY.md
   └── Registrar convenções novas adotadas
   └── Registrar lacunas encontradas mas fora do escopo
   └── Atualizar mapa de documentação existente

6. RETORNAR AO CEO
   └── Lista de arquivos produzidos com caminho completo
   └── Audiência de cada documento
   └── Pontos ambíguos encontrados no código e como foram interpretados
   └── Lacunas de documentação que ficaram fora do escopo
```

---

## Tipos de documento e seus templates mentais

### README
```
# Nome do Projeto
Descrição em 2 frases.

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

**Request**
- Headers obrigatórios
- Body (schema + exemplo)

**Response**
- 200: schema + exemplo
- 4xx: casos de erro

**Exemplo completo** (cURL ou código)
```

### ADR (Architecture Decision Record)
```
# ADR-NNN: Título
**Data**: YYYY-MM-DD
**Status**: Aceito / Depreciado / Substituído por ADR-XXX

## Contexto
## Decisão
## Consequências
## Alternativas consideradas
```

### Changelog (Keep a Changelog)
```
## [versão] - YYYY-MM-DD
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
```
