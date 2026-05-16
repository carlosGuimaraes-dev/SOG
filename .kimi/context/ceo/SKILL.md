# Skills Disponíveis — CEO

Este arquivo lista as skills reutilizáveis à disposição deste agente.
Para usar uma skill, leia seu SKILL.md antes de orquestrar.

---

## Orchestration Patterns
**Use quando:** definir fluxos de trabalho, delegar a agentes, estabelecer critérios de aceite ou decidir quando escalar ao usuário.
**Arquivo:** `.kimi/skills/orchestration-patterns/SKILL.md`
**Prioridade:** ALTA

---

## Skills por Agente Subordinado

| Agente | Skills Principais | Caminho |
|--------|------------------|---------|
| CTO | architecture-decisions, tech-stack-analysis | `.kimi/skills/` |
| Dev Senior | playwright-scraper, fastapi-backend, sqlite-patterns, pdf-processor, python-testing | `.kimi/skills/` |
| Frontend | react-vite-frontend, tailwind-shadcn, frontend-testing, frontend-accessibility | `.kimi/skills/` |
| DevOps | docker-compose-infra, nginx-proxy, github-actions-ci | `.kimi/skills/` |
| QA | qa-validation, pytest-runner, frontend-test-runner | `.kimi/skills/` |
| Reviewer | code-review-security, python-code-quality, frontend-code-quality | `.kimi/skills/` |
| Docs Writer | technical-documentation, api-documentation | `.kimi/skills/` |

---

## Como criar uma nova skill

Quando o projeto evoluir e surgir a necessidade de uma skill que não existe:

1. **Identifique a lacuna**: qual domínio ou padrão se repete e não está coberto?
2. **Use a skill `skill-creator`**: leia `~/.agents/skills/karpathy-guidelines/SKILL.md` para boas práticas
3. **Estrutura obrigatória**:
   - Crie diretório em `.kimi/skills/<nome-da-skill>/`
   - Arquivo `SKILL.md` com frontmatter YAML (`name`, `description`)
   - Corpo com: resumo → quando usar → padrões principais → exemplos → anti-patterns
   - Máximo 500 linhas; use `references/` e `scripts/` para conteúdo adicional
4. **Atualize o SKILL.md do agente**: adicione a nova skill em `.kimi/context/<agente>/SKILL.md`
5. **Valide**: verifique frontmatter, nomes e se a skill é relevante ao domínio SOG

**Quando criar uma nova skill:**
- Um padrão se repete em 3+ tarefas diferentes
- Um agente precisa de conhecimento especializado não coberto (ex.: PostgreSQL, Redis, Kubernetes)
- Uma integração com sistema externo se torna recorrente

**NÃO crie skill para:**
- Tarefas únicas ou pontuais
- Conhecimento que o modelo já possui genericamente
- Abstrações de código que devem viver no projeto, não em skill

---

## Como adaptar a equipe a um novo projeto

Quando a fábrica for deslocada para outro repositório/projeto:

1. **Analise o novo projeto**
   - Leia `README.md`, `package.json`, `pyproject.toml`, `requirements.txt`, `Dockerfile`
   - Identifique stack, frameworks, linguagens e domínio de negócio
   - Use `Glob` para mapear a estrutura do codebase

2. **Avalie skills existentes**
   - Compare stack do novo projeto com as 23 skills disponíveis
   - Skills genéricas (ex.: `python-code-quality`, `frontend-accessibility`) → reutilizar
   - Skills de domínio (ex.: `playwright-scraper`, `pdf-processor`) → avaliar relevância
   - Skills faltantes para a nova stack → marcar para criação

3. **Crie skills específicas do novo projeto**
   - Siga o processo em **"Como criar uma nova skill"** acima
   - Priorize: autenticação do novo domínio, APIs específicas, padrões de UI
   - Exemplo: projeto com PostgreSQL → criar `postgres-patterns`

4. **Atualize SKILL.md de cada agente**
   - Substitua a lista de skills em cada `.kimi/context/<agente>/SKILL.md`
   - Mantenha skills genéricas; remova/adicione conforme o novo domínio
   - Atualize prioridades (ALTA/MÉDIA/BAIXA) para o novo contexto

5. **Delete completamente as memórias antigas**
   - Delete `MEMORY.md` de **todos** os agentes: `.kimi/context/*/MEMORY.md`
   - Projetos distintos exigem memórias novas — nunca carregue contexto de projeto anterior
   - O novo `MEMORY.md` será criado do zero pelo CTO após a primeira análise
   - **Exceção**: o `MEMORY.md` do CEO pode preservar apenas o índice de projetos ativos (nomes e datas), nunca detalhes técnicos

6. **Valide**
   - Confirme que todos os agentes têm pelo menos 2 skills relevantes
   - Verifique que não há skills órfãs (listadas no agente mas sem arquivo)

**Quando fazer isso:**
- Ao receber ordem explícita do usuário de mudar de projeto
- Ao detectar que o `KIMI_WORK_DIR` mudou para outro repositório
- Antes da primeira tarefa no novo projeto

**NÃO faça isso:**
- Sem ordem explícita do usuário
- Durante uma tarefa em andamento no projeto atual
- Automaticamente — sempre confirme com o usuário

---

## Como usar uma skill

1. Ao briefar um agente, verifique se há skills relevantes ao escopo da tarefa
2. Inclua no prompt do agente: "Consulte SKILL.md no seu contexto para skills disponíveis"
3. O agente subordinado lerá a skill antes de executar
4. Use `orchestration-patterns` para definir fluxos complexos
