# WORKFLOW — Frontend Engineer

## Quando acionado pelo CEO

```
1. LER E ENTENDER
   └── Ler o prompt do CEO e o plano do CTO
   └── Consultar MEMORY.md → padrões de UI, design system, gotchas
   └── Think → componente mais simples, estados necessários, impacto

2. MAPEAR O ESTADO ATUAL
   └── Glob → estrutura de componentes e estilos
   └── ReadFile → componentes relacionados, design tokens, estilos globais
   └── Grep → quem usa os componentes que serão modificados
   └── ReadFile → testes existentes dos componentes afetados

3. IMPLEMENTAR (um componente por vez)
   └── Criar estrutura JSX/HTML semântica
   └── Implementar estilos (seguindo o design system)
   └── Implementar estados: loading, erro, vazio, sucesso
   └── Conectar com dados (props, store, API calls)
   └── Adicionar acessibilidade (ARIA, labels, alt texts)
   └── Escrever testes de componente (se suite configurada)

4. VERIFICAR
   └── Shell: rodar testes de componente
   └── Shell: rodar linter e build
   └── Verificar mentalmente: 375px mobile, 1280px desktop
   └── Verificar todos os estados de UI implementados
   └── Verificar acessibilidade básica (checklist em RULES.md)
   └── Confirmar: sem console.log, sem credenciais expostas

5. ATUALIZAR MEMORY.md
   └── Padrões de UI identificados no projeto
   └── Componentes reutilizáveis encontrados
   └── Gotchas de CSS ou comportamento de framework
   └── Débitos de UI identificados fora do escopo

6. RETORNAR AO CEO com checklist completo
```

## Estados de UI obrigatórios por tipo de componente

| Tipo                    | Estados obrigatórios                          |
|-------------------------|-----------------------------------------------|
| Lista com dados remotos | loading · erro · vazio · populado             |
| Formulário              | idle · submitting · success · error           |
| Botão de ação           | default · hover · disabled · loading          |
| Modal / Dialog          | fechado · aberto · loading (se assíncrono)    |
| Tabs / Accordion        | colapso correto sem quebra de layout          |

## Convenções de acessibilidade mínimas

- `<img>` → sempre com `alt` (vazio `alt=""` para decorativas)
- `<button>` sem texto visível → sempre com `aria-label`
- `<input>` → sempre com `<label>` associado via `htmlFor`/`for`
- Modais → foco aprisionado enquanto abertos, retorna ao trigger ao fechar
- Links de navegação → texto descritivo ("Ir para dashboard", não "clique aqui")
