# Skills Disponíveis — Reviewer

Este arquivo lista as skills reutilizáveis à disposição deste agente.
Para usar uma skill, leia seu SKILL.md antes de revisar.

---

## Code Review Security
**Use quando:** revisar código focando em segurança: OWASP, injeção, autenticação, secrets, headers.
**Arquivo:** `.kimi/skills/code-review-security/SKILL.md`
**Prioridade:** ALTA

## Python Code Quality
**Use quando:** revisar código Python: PEP 8, type hints, complexidade, docstrings, organização.
**Arquivo:** `.kimi/skills/python-code-quality/SKILL.md`
**Prioridade:** MÉDIA

## Frontend Code Quality
**Use quando:** revisar código frontend: ESLint, TypeScript, organização, props, memoização.
**Arquivo:** `.kimi/skills/frontend-code-quality/SKILL.md`
**Prioridade:** MÉDIA

---

## Como usar uma skill

1. Antes de revisar, verifique se há uma skill relevante para o código sob review
2. Leia o SKILL.md da skill com `ReadFile`
3. Use os checklists de qualidade como guia sistemático
4. Classifique findings conforme os critérios da skill (BLOQUEADOR/ATENÇÃO/SUGESTÃO)
