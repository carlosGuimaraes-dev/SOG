---
name: qa-validation
description: >
  Use para validação funcional, relatórios de QA e regressão.
  Inclui checklist de validação, classificação de severidade,
  template de relatório, edge cases e validação requisitos vs implementação.
---

# qa-validation

Validação funcional e relatórios de QA.

## Quando usar

- Antes de mergear PRs críticos.
- Após deploy em staging para homologação.
- Ao receber feedback de regressão em produção.
- Para validar que requisitos foram corretamente implementados.

## Padrões principais

### Checklist de validação

- [ ] Funcionalidade principal executa conforme especificação.
- [ ] Validações de entrada rejeitam dados inválidos.
- [ ] Mensagens de erro são claras e localizadas.
- [ ] Estados de loading, vazio e erro estão cobertos.
- [ ] Responsividade / diferentes viewports (se aplicável).
- [ ] Permissões e roles funcionam corretamente.
- [ ] Navegação e fluxo de telas estão intuitivos.

### Classificação de severidade

| Severidade | Definição | Tempo de resposta |
|-----------|-----------|-------------------|
| BLOQUEADOR | Impede uso da funcionalidade ou crash. | Imediato |
| ALTO | Funcionalidade principal comprometida com workaround difícil. | < 24h |
| MÉDIO | Funcionalidade secundária afetada ou workaround fácil. | < 3 dias |
| BAIXO | Cosmético, typo, melhoria de UX. | Próxima sprint |

### Template de relatório

```markdown
## Resumo
- Funcionalidade: Login com OAuth
- Ambiente: Staging
- Data: 2024-06-01

## Severidade: ALTO

### Descrição
Redirecionamento para callback retorna 500 quando email não está verificado.

### Passos para reproduzir
1. Criar conta via OAuth sem verificar email.
2. Tentar login.

### Esperado
Redirecionar para tela de verificação com mensagem informativa.

### Obtido
Erro 500 genérico.

### Evidências
- Screenshot: login-error-500.png
- Log: staging-api-20240601.log

### Sugestão
Tratar `email_verified=False` no handler de callback.
```

### Regressão

- Identificar área afetada pela mudança.
- Executar suite de testes existentes na funcionalidade.
- Verificar se defeitos corrigidos anteriormente reapareceram.
- Documentar no relatório quais fluxos foram verificados para regressão.

### Edge cases

| Cenário | Descrição |
|---------|-----------|
| Dados vazios | Campos obrigatórios em branco |
| Dados extremos | Strings de 1MB, números negativos |
| Concorrência | Múltiplas requisições simultâneas |
| Timeout | API lenta ou indisponível |
| Caracteres especiais | Emojis, HTML, SQL injection attempts |

### Validação de requisitos vs implementação

1. Liste os requisitos funcionais do PRD/ticket.
2. Para cada requisito, marque: ✅ Implementado / ❌ Não implementado / ⚠️ Parcial.
3. Anote divergências com severidade correspondente.
4. Anexe evidências (screenshots, logs, vídeos).

## Anti-patterns

- Relatar apenas "não funciona" sem passos de reprodução.
- Classificar tudo como BLOQUEADOR → priorização perde sentido.
- Ignorar edge cases porque "usuário nunca vai fazer isso".
- Não verificar regressão em funcionalidades adjacentes.
