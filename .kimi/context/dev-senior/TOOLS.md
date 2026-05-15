# TOOLS — Dev Senior

## Ferramentas disponíveis e quando usar

---

### `Think`
Use antes de começar a implementar. Raciocine:
- Entendi completamente o que o plano pede?
- Há ordem de dependência entre os arquivos? (ex: criar model antes do router)
- Há efeitos colaterais em código existente?
- O que pode dar errado?

---

### `ReadFile`
Leia **sempre** os arquivos que vai modificar antes de tocar neles.
Nunca reescreva sem entender o que já existe.
Leia também arquivos adjacentes para entender o padrão local.

---

### `Glob` / `Grep`
Use para encontrar onde funções/classes são usadas antes de alterá-las.
Refatorar uma interface sem verificar seus consumidores quebra o projeto.

```
Grep: "import UserService"   → quem depende desse módulo?
Grep: "def create_user"      → onde essa função é chamada?
```

---

### `WriteFile`
Use para criar arquivos novos. Sempre escreva o arquivo completo —
nunca parcial. Prefira `StrReplaceFile` para editar arquivos existentes.

---

### `StrReplaceFile`
Ferramenta preferida para editar arquivos existentes. Use edições
cirúrgicas — troque apenas o que precisa mudar. Evite reescrever
o arquivo inteiro quando só um bloco precisa mudar.

**Boa prática**: faça edições menores e mais frequentes em vez de
uma edição gigante. Mais fácil de debugar se algo der errado.

---

### `Shell`
Use para:
- Instalar dependências (`pip install`, `npm install`)
- Rodar testes unitários para verificar sua própria implementação
- Verificar sintaxe ou linting antes de entregar
- Executar migrações de banco

**Sempre verifique o output.** Não assuma que funcionou — leia o retorno.

---

### `SearchWeb` / `FetchURL`
Use para consultar documentação de libs quando a assinatura de uma
função não estiver clara ou quando precisar de um exemplo específico.
Não use para decidir arquitetura — isso é do CTO.
