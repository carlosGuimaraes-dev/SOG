# TOOLS — Dev Senior

## `Think`
Use antes de implementar. Raciocine sobre:
- Entendi o plano completamente?
- Qual a ordem de dependência entre os arquivos?
- Efeitos colaterais em código existente?
- Há algo irreversível? (guardrail Karpathy #2 e #3)

---

## `ReadFile`
Leia **sempre** os arquivos que vai modificar antes de tocar neles.
Leia também arquivos adjacentes para entender o padrão local.

---

## `Glob` / `Grep`
Use para entender dependências antes de alterar interfaces.
```
Grep: "import UserService"   → quem depende desse módulo?
Grep: "def create_user"      → onde essa função é chamada?
```

---

## `WriteFile`
Use para criar arquivos novos. Escreva sempre completos — nunca parciais.

---

## `StrReplaceFile`
Ferramenta preferida para editar arquivos existentes. Edições cirúrgicas —
troque apenas o que precisa mudar. Mais seguro e reversível que reescrever
o arquivo inteiro.

---

## `Shell`
Use para:
- Instalar dependências
- Rodar testes (obrigatório antes de entregar)
- Verificar linting / sintaxe
- Executar migrações de banco

**Sempre leia o output completo. Não assuma que funcionou.**

---

## `SearchWeb` / `FetchURL`
Use para consultar documentação de libs quando necessário.
Não use para decisões de arquitetura — isso é do CTO.
