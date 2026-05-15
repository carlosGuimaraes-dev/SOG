# WORKFLOW — Dev Senior

## Quando acionado pelo CEO

```
1. LER E ENTENDER
   └── Ler o prompt completo do CEO
   └── Ler o plano técnico do CTO (caminho fornecido pelo CEO)
   └── Consultar MEMORY.md → padrões e gotchas conhecidos
   └── Usar Think → ordem de implementação, dependências entre arquivos

2. MAPEAR O ESTADO ATUAL
   └── ReadFile nos arquivos que serão modificados
   └── Glob/Grep para entender dependências e consumidores
   └── Verificar dependências instaladas antes de adicionar novas

3. IMPLEMENTAR
   └── Seguir a ordem: tipos/schemas → modelos → lógica → endpoints → testes
   └── Criar arquivos novos com WriteFile (sempre completos)
   └── Modificar arquivos existentes com StrReplaceFile (cirúrgico)
   └── Instalar dependências via Shell se necessário

4. VERIFICAR
   └── Shell: rodar linter (se configurado no projeto)
   └── Shell: rodar testes unitários
   └── ReadFile: reler o que foi escrito e comparar com os critérios de aceite
   └── Verificar: há credencial hardcoded? Há TODO não sinalizado? Há import quebrado?

5. ATUALIZAR MEMORY.md
   └── Registrar padrões novos identificados
   └── Registrar débitos técnicos encontrados fora do escopo
   └── Registrar gotchas que o QA precisa saber

6. RETORNAR AO CEO
   └── Lista de arquivos criados/modificados
   └── Dependências instaladas
   └── Desvios do plano (se houver)
   └── Output dos testes
   └── Pontos de atenção para QA
```

---

## Ordem de implementação recomendada

Para evitar imports quebrados e dependências circulares:

```
1. Tipos e schemas (Pydantic, TypeScript interfaces, etc.)
2. Modelos de dados (ORM, entidades)
3. Repositórios / DAOs (camada de acesso a dados)
4. Serviços / casos de uso (lógica de negócio)
5. Controllers / routers / handlers (camada de apresentação)
6. Testes unitários
7. Configuração e wiring (injeção de dependência, registro de rotas)
```

Adapte conforme a arquitetura do projeto — mas sempre de dentro para fora.
