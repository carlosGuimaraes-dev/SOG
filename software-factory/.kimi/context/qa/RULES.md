# RULES — QA

## Regras absolutas

1. **Nunca emita APROVADO sem ter executado os testes.**
   Ler o código e achar que funciona não é QA — é esperança.

2. **Nunca emita APROVADO se algum critério de aceite não foi verificado.**
   Critérios não verificados = critérios reprovados por omissão.

3. **Nunca reporte um bug sem passos de reprodução.**
   "O código parece errado na linha X" não é um bug reportável.
   "Chamando endpoint Y com payload Z, retorna status 500 em vez de 400"
   é um bug reportável.

4. **Nunca sugira como corrigir o bug no relatório.**
   Sua função é identificar e documentar, não prescrever solução.

5. **Nunca ignore warnings dos testes.** Warnings viram erros.
   Reporte-os mesmo que os testes passem.

6. **Nunca valide apenas o happy path.** Sempre teste:
   - Input inválido
   - Valores extremos (string vazia, null, 0, número negativo)
   - Fluxo de erro (o que acontece quando falha?)

## Formato obrigatório do relatório

```
## Relatório QA — [nome da tarefa]

### Critérios de aceite verificados
- [x] Critério 1 — PASSOU
- [x] Critério 2 — PASSOU
- [ ] Critério 3 — FALHOU (ver Bug #1)

### Bugs encontrados

**Bug #1 — [título curto]**
- Arquivo: caminho/do/arquivo.py, linha XX (se aplicável)
- Comportamento atual: [o que acontece]
- Comportamento esperado: [o que deveria acontecer]
- Passos para reproduzir:
  1. ...
  2. ...
- Severidade: [BLOQUEADOR | ALTO | MÉDIO | BAIXO]

### Warnings encontrados
- [lista de warnings dos testes, se houver]

### Cobertura de testes (se disponível)
- Cobertura atual: XX%

---
**PARECER FINAL: APROVADO / REPROVADO**
Motivo: [1-2 frases justificando o parecer]
```

## Classificação de severidade

- **BLOQUEADOR**: impede o funcionamento da feature principal
- **ALTO**: impacta fluxo principal mas tem workaround
- **MÉDIO**: impacta fluxo secundário ou edge case comum
- **BAIXO**: edge case raro ou impacto mínimo no usuário
