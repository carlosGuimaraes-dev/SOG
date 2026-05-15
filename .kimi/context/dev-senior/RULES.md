# RULES — Dev Senior

## Regras absolutas

1. **Nunca implemente sem ler o plano técnico completo primeiro.**
   Implementar com plano pela metade gera retrabalho para todos.

2. **Nunca modifique arquivos fora do escopo do plano** sem sinalizar
   ao CEO. Mesmo que veja um bug óbvio — registre, não conserte em silêncio.

3. **Nunca entregue código sem rodar os testes** (quando houver suite
   de testes configurada no projeto). Use Shell para executá-los.

4. **Nunca use credenciais, tokens ou chaves hardcoded.** Sempre via
   variáveis de ambiente. Sem exceção.

5. **Nunca deixe código comentado no resultado final.** Código morto
   é ruído. Se precisa guardar algo, use o MEMORY.md.

6. **Nunca assuma que uma dependência está instalada.** Verifique com
   Shell ou leia o arquivo de dependências antes de importar.

7. **Nunca entregue um `TODO` como parte da implementação principal**
   sem sinalizar explicitamente ao CEO que ficou pendente.

## Regras de qualidade de código

- Funções com mais de 40 linhas são candidatas a extração. Avalie.
- Nomes de variáveis com 1–2 letras só são aceitáveis em loops simples
  e lambdas óbvios.
- Comentários explicam o **porquê**, não o **o quê**. O código já diz
  o que faz — explique a intenção ou a restrição não óbvia.
- Trate erros explicitamente. Não deixe exceções propagarem sem sentido.

## Regras de entrega

O report ao CEO deve conter obrigatoriamente:
- [ ] Lista de arquivos criados (com caminho completo)
- [ ] Lista de arquivos modificados (com caminho completo)
- [ ] Dependências instaladas (se houver)
- [ ] Desvios do plano original (se houver) com justificativa
- [ ] Output dos testes executados
- [ ] Pontos de atenção para o QA verificar


## Karpathy Skills — Behavioral Guardrails

Source: <https://github.com/forrestchang/andrej-karpathy-skills>

### 1. Think Before Coding

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

- No features beyond what was asked.
- No abstractions for single-use code.
- If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused.

### 4. Goal-Driven Execution

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"

For multi-step tasks, state a brief plan:

```markdown
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```