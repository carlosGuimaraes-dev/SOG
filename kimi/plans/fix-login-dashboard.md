# Plano Técnico — Correção do Login no Dashboard SOG

## 1. Diagnóstico

### 1.1 Hash de senha corrompido no `.env.api`
- **Arquivo afetado:** `.env.api`
- **Valor atual:** `DASHBOARD_SENHA_HASH=$$2b$$12$$XAQoPaBNEfabrljW07OG2.5nWx8MDgiaPGum4korv7ndtYQDqg3Pa`
- **Problema:** Os `$` foram duplicados para `$$` (provável artefato de escaping de Docker Compose ou copia de template). Quando o Python lê a variável, recebe a string literal com `$$`.
- **Impacto:** A função `_hash_valido()` em `api/src/auth.py` rejeita o hash porque ele não começa com os prefixos bcrypt válidos (`$2a$`, `$2b$`, `$2x$`, `$2y$`). Como resultado, `authenticate_user()` retorna `False` para **qualquer** senha digitada.

### 1.2 Incompatibilidade `passlib` × `bcrypt` no container da API
- **Versões instaladas:** `passlib==1.7.4` + `bcrypt==5.0.0`
- **Problema:** O `passlib` 1.7.4 não é compatível com `bcrypt>=4.1` (e muito menos 5.0.0). Qualquer chamada a `pwd_context.verify()` ou `pwd_context.hash()` levanta exceção (`AttributeError: module 'bcrypt' has no attribute '__about__'` ou `ValueError: password cannot be longer than 72 bytes`).
- **Impacto:** Mesmo que o hash no `.env.api` fosse corrigido, a verificação de senha ainda falharia e o login continuaria impossível.

### 1.3 Frontend — OK
- `frontend/src/pages/Login.tsx` captura usuário/senha corretamente.
- `frontend/src/lib/auth.tsx` envia payload `{ username, password }` via POST para `/api/v1/auth/login`.
- O schema `LoginRequest` no backend (`username: str`, `password: str`) corresponde exatamente ao payload enviado.
- **Conclusão:** O frontend não é a causa da falha.

### 1.4 Backend schema — OK
- O endpoint `POST /auth/login` em `api/src/rotas/auth.py` está correto e bem estruturado (cookies httpOnly, rate-limit, refresh-token rotation).
- A lógica de autenticação em `api/src/auth.py` é semanticamente correta; ela apenas depende de bibliotecas quebradas e de um hash de ambiente inválido.

---

## 2. Ação Corretiva

> **Abordagem escolhida:** Corrigir o hash no `.env.api` **e** substituir o uso do `passlib` por `bcrypt` puro em `api/src/auth.py`. Isso evita rebuild de imagem Docker e resolve a incompatibilidade de forma definitiva.

### Passo 2.1 — Gerar novo hash bcrypt válido
Execute dentro do container `custas-api` (ou em qualquer ambiente com `bcrypt` funcional):

```bash
docker exec custas-api python -c "
import bcrypt
print(bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode())
"
```

> **Nota:** troque `b'admin'` pela senha desejada. Cada execução gera um hash diferente (salt aleatório); qualquer um deles será válido.

### Passo 2.2 — Corrigir `.env.api`
Atualize a linha `DASHBOARD_SENHA_HASH` para usar `$` simples (copie o hash gerado no passo anterior):

```bash
# Exemplo (substitua pelo hash real gerado acima):
DASHBOARD_SENHA_HASH=$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> ⚠️ **Atenção:** Não use `$$`. O valor deve ser um hash bcrypt canônico, começando com `$2b$`.

### Passo 2.3 — Substituir `passlib` por `bcrypt` puro em `api/src/auth.py`

Altere a seção de "Password helpers" (~linhas 32-49):

```python
# REMOVER:
# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ADICIONAR no topo do arquivo:
import bcrypt

# Substituir as funções:
def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or len(hashed) < 10:
        return False
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

**Impacto da mudança:**
- `bcrypt` já está instalado no container (é dependência transitiva de `passlib[bcrypt]`).
- Não é necessário rebuild de imagem; basta reiniciar o container.
- Os testes existentes (`api/tests/`) não referenciam `passlib` diretamente, portanto não quebram.

### Passo 2.4 — Reiniciar o container da API

```bash
docker-compose restart api
# ou, se estiver usando dev:
docker-compose -f docker-compose.dev.yml restart api
```

### Passo 2.5 — Verificar logs de startup

```bash
docker logs custas-api | tail -n 20
```

Certifique-se de que não aparece o erro:
```
DASHBOARD_SENHA_HASH ausente ou inválido. Aplicação não pode iniciar.
```

---

## 3. Critérios de Aceite

- [ ] Usuário consegue acessar a tela de login (`/login`) do dashboard.
- [ ] Usuário digita `admin` / `admin` (ou a senha definida no Passo 2.1) e o login é bem-sucedido.
- [ ] Após o login, o frontend redireciona para o dashboard (`/`).
- [ ] A rota `/api/v1/auth/me` retorna `{"username": "admin"}`.
- [ ] O cookie `access_token` é criado com flags `HttpOnly`, `Secure` (produção) e `SameSite`.
- [ ] Os testes da API (`pytest api/tests/`) continuam passando.

---

## 4. Ações Irreversíveis

- **Mudança do hash em `.env.api`:** Se o hash anterior (`$$2b$$...`) correspondia a uma senha antiga que alguém ainda possa tentar usar, essa senha deixará de funcionar permanentemente após a correção.
- **Substituição do `passlib`:** A remoção do `passlib` do `auth.py` é irreversível no sentido de que, se no futuro for necessário suportar múltiplos algoritmos de hash, será preciso reintroduzir uma camada de abstração. Para o escopo atual (apenas bcrypt), a mudança é segura e preferível.
- **Rebuild não necessário:** Como a correção é feita via volume mount (`./api/src:/app/src:ro` no dev) ou editando o arquivo dentro do container, não há alteração na imagem Docker. Se for necessário recriar o container a partir da imagem base, as mudanças no `auth.py` precisarão estar commitadas no repo.