---
name: api-documentation
description: Use ao documentar, consumir ou revisar APIs. Aplica-se a APIs REST, GraphQL, webhooks e bibliotecas clientes. Foca na clareza para consumidores e na redução de suporte.
---

# Documentação de APIs

## Resumo

Documentação de API é contrato. Ela deve permitir que um desenvolvedor desconhecido com o projeto faça sua primeira requisição bem-sucedida em menos de 10 minutos. Isso exige exemplos funcionais, descrição clara de erros e informações de autenticação acessíveis.

## Quando usar

- Ao criar ou modificar endpoints
- Ao expor API para consumidores externos
- Durante revisão de código de controllers/rotas
- Ao onboardar integradores ou frontends
- Quando surgem dúvidas repetidas sobre uso da API

## Padrões principais

### OpenAPI/Swagger

Use FastAPI (gera automaticamente) ou escreva `openapi.yaml` manualmente para outras stacks.

```yaml
openapi: 3.0.3
info:
  title: API de Custas
  version: 1.0.0
paths:
  /custas:
    post:
      summary: Consulta custas de processo
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                numero_processo:
                  type: string
                  example: "0001234-12.2024.8.07.0012"
      responses:
        200:
          description: Custas encontradas
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustasResponse'
```

Regras:
- Todos os endpoints devem estar documentados
- Todos os campos de request/response devem ter `description`
- Use `example` para todos os campos string
- Agrupe endpoints por tag lógica

### Exemplos de requisição/resposta

Cada endpoint deve ter exemplos mínimos:

**Requisição:**
```bash
curl -X POST https://api.exemplo.com/v1/custas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbG..." \
  -d '{"numero_processo": "0001234-12.2024.8.07.0012"}'
```

**Resposta 200:**
```json
{
  "numero_processo": "0001234-12.2024.8.07.0012",
  "total": 1250.0,
  "itens": [
    {"descricao": "Taxa de inicial", "valor": 250.0, "data": "2024-01-15"}
  ]
}
```

**Resposta 422 (validação):**
```json
{
  "detail": [
    {"loc": ["body", "numero_processo"], "msg": "Formato inválido", "type": "value_error"}
  ]
}
```

### Códigos de erro

Documente todos os códigos HTTP que o endpoint pode retornar:

| Código | Quando ocorre | Corpo da resposta |
|--------|---------------|-------------------|
| 200 | Sucesso | `CustasResponse` |
| 401 | Token ausente ou inválido | `{"detail": "Não autenticado"}` |
| 403 | Token válido, sem permissão | `{"detail": "Sem permissão"}` |
| 422 | Dados de entrada inválidos | `HTTPValidationError` |
| 429 | Rate limit excedido | `{"detail": "Rate limit excedido", "retry_after": 60}` |
| 500 | Erro interno | `{"detail": "Erro interno", "request_id": "uuid"}` |

Nunca retorne 500 sem um `request_id` rastreável.

### Autenticação

Documente explicitamente:

1. **Método** — Bearer token, API key, OAuth2
2. **Como obter** — endpoint de login, variável de ambiente, portal
3. **Expiração** — tempo de vida do token
4. **Renovação** — como refreshar
5. **Exemplo completo** — do login à requisição autenticada

```markdown
## Autenticação

Todas as requisições requerem um Bearer token no header
`Authorization`.

### Obter token
```bash
curl -X POST https://api.exemplo.com/auth/token \
  -d "username=admin&password=secret"
```

O token expira em 24h. Use `/auth/refresh` para renovar.
```

### Rate limits

Documente limites por endpoint e por usuário:

```markdown
| Endpoint | Limite | Janela |
|----------|--------|--------|
| POST /custas | 10/min | IP |
| GET /processos | 100/min | API key |
| Todos | 1000/hora | API key |
```

Inclua headers de rate limit nas respostas:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1715798400
```

### Versionamento

Use versionamento de URL: `/v1/`, `/v2/`.

Regras:
- Quebras de contrato (remover campo, mudar tipo) → nova versão
- Adições de campos opcionais → mesma versão
- Depreciação → mantenha versão antiga por 6 meses com header `Deprecation`
- Sunset → header `Sunset: <data>` com 3 meses de antecedência

```
Deprecation: true
Sunset: Wed, 31 Dec 2026 23:59:59 GMT
```

### Coleções Postman/Insomnia

Exporte coleções da API para:

- Onboarding rápido de novos devs
- Testes de integração manuais
- Compartilhamento com parceiros externos

Nomeie requests e folders de forma consistente:

```
Custas API v1
├── Auth
│   ├── Login
│   └── Refresh Token
├── Custas
│   ├── Consultar Custas
│   └── Listar Processos
└── Health
    └── Check
```

Use environments para base URL e tokens:

| Variable | Local | Staging | Production |
|----------|-------|---------|------------|
| base_url | http://localhost:8000 | https://staging... | https://api... |
| token | (login manual) | (login manual) | (login manual) |

## Exemplos

### Documentação de endpoint com todos os elementos

```markdown
### POST /v1/custas

Consulta custas processuais de um número de processo.

#### Autenticação
Bearer token obrigatório.

#### Request
```json
{
  "numero_processo": "0001234-12.2024.8.07.0012"
}
```

#### Responses

**200 OK**
```json
{
  "numero_processo": "0001234-12.2024.8.07.0012",
  "total": 1250.0,
  "itens": [...]
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [{"loc": ["body", "numero_processo"], "msg": "Formato inválido"}]
}
```

**429 Too Many Requests**
```json
{"detail": "Rate limit excedido", "retry_after": 60}
```
```

## Anti-patterns

- **Sem exemplos** — documentação de schema sem requisição/resposta real
- **Erros genéricos** — "pode retornar 4xx" sem especificar qual e quando
- **Autenticação escondida** — documentada em lugar separado e difícil de encontrar
- **Sem versionamento** — quebras de contrato sem aviso prévio
- **Coleções desatualizadas** — Postman com endpoints que não existem mais
- **Rate limit não documentado** — consumidores descobrem por trial-and-error
