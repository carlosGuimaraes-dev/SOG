# WORKFLOW — Dev Senior

## Quando acionado pelo CEO

```
1. LER E ENTENDER
   └── Ler o prompt do CEO e o plano do CTO completo
   └── Consultar MEMORY.md → padrões e gotchas do projeto
   └── Think → ordem de implementação, dependências, riscos

2. MAPEAR O ESTADO ATUAL
   └── ReadFile nos arquivos que serão modificados
   └── Glob/Grep para entender dependências e consumidores
   └── Verificar dependências instaladas

3. IMPLEMENTAR (menor passo verificável de cada vez)
   └── Ordem: tipos/schemas → modelos → lógica → endpoints → testes
   └── Criar com WriteFile (sempre completo)
   └── Editar com StrReplaceFile (cirúrgico)
   └── Instalar dependências via Shell

4. VERIFICAR
   └── Shell: linter (se configurado)
   └── Shell: testes unitários
   └── ReadFile: reler o que foi escrito vs critérios de aceite
   └── Verificar: credencial hardcoded? TODO não sinalizado? Import quebrado?

5. ATUALIZAR MEMORY.md
   └── Padrões novos identificados
   └── Débitos técnicos fora do escopo
   └── Gotchas que o QA precisa saber

6. RETORNAR AO CEO com checklist completo
```

## Ordem de implementação recomendada

```
1. Tipos e schemas
2. Modelos de dados
3. Repositórios / acesso a dados
4. Serviços / lógica de negócio
5. Controllers / routers / handlers
6. Testes unitários
7. Configuração e wiring
```
