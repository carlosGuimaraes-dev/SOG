---
name: code-review-security
description: >
  Use para code review focado em segurança.
  Inclui OWASP Top 10, injeção SQL/XSS, autenticação/autorização,
  secrets hardcoded, validação de entrada, headers de segurança e
  classificação de findings (BLOQUEADOR/ATENÇÃO/SUGESTÃO).
---

# code-review-security

Code review focado em segurança.

## Quando usar

- Revisar PRs que alteram autenticação, autorização ou parsing de dados.
- Revisar integrações com APIs externas.
- Antes de deploys em produção.
- Ao adicionar novas dependências ou bibliotecas de criptografia.

## Padrões principais

### OWASP Top 10 — checklist rápido

1. **Broken Access Control**: Verificar se endpoints verificam permissões.
2. **Cryptographic Failures**: Dados sensíveis criptografados em trânsito e repouso.
3. **Injection**: Queries parametrizadas; nunca concatenar input direto.
4. **Insecure Design**: Rate limiting, validação de negócio no backend.
5. **Security Misconfiguration**: Headers de segurança, configs padrão removidas.
6. **Vulnerable Components**: Dependências desatualizadas com CVEs.
7. **Authentication Failures**: Senhas fortes, 2FA, sessões seguras.
8. **Software Integrity**: Verificar integridade de pacotes/artefatos.
9. **Logging Failures**: Não logar senhas ou tokens; logar tentativas de acesso.
10. **SSRF**: Validação de URLs em requisições server-side.

### Injeção SQL / XSS

```python
# ✅ SQL parametrizada
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ Concatenação insegura
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

```python
# ✅ Escape de output em templates
from markupsafe import Markup, escape
rendered = escape(user_input)

# ❌ Renderizar input do usuário sem sanitização
html = f"<div>{user_input}</div>"
```

### Autenticação / Autorização

- Verificar se todas as rotas protegidas exigem autenticação.
- Confirmar que autorização verifica ownership do recurso.
- Garantir que tokens/JWT têm expiry e são revogáveis.
- Nunca confiar apenas em `user_id` vindo do cliente sem validação.

### Secrets hardcoded

```python
# ❌
API_KEY = "sk-1234567890abcdef"

# ✅
import os
API_KEY = os.environ.get("API_KEY")
```

### Validação de entrada

```python
from pydantic import BaseModel, validator

class LoginRequest(BaseModel):
    email: str
    password: str

    @validator("email")
    def validar_email(cls, v):
        if "@" not in v:
            raise ValueError("email inválido")
        return v
```

### Headers de segurança

- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`

### Classificação de findings

| Classificação | Critério | Ação |
|--------------|----------|------|
| BLOQUEADOR | Risco imediato de vazamento de dados ou comprometimento de sistema. | Deve ser corrigido antes do merge. |
| ATENÇÃO | Potencial vulnerabilidade ou prática insegura com impacto moderado. | Deve ser corrigido na sprint atual. |
| SUGESTÃO | Melhoria de segurança ou hardening sem risco imediato. | Pode ser endereçado futuramente. |

## Anti-patterns

- Validar apenas no frontend → bypass trivial.
- Confiança em `is_admin: true` vindo do cliente.
- Logar tokens, senhas ou PII.
- Desabilitar verificação SSL em produção (`verify=False`).
- Usar `eval()` ou `exec()` com input não confiável.
