# SOP: Entrega Versionada por Agentes

Esta SOP é obrigatória para qualquer agente que altere arquivos do projeto SOG.

Uma tarefa não está concluída porque um arquivo foi editado no workspace. Uma
tarefa só está concluída quando a alteração necessária está versionada, publicada
e rastreável no fluxo correto do repositório.

## Regra Absoluta

Nunca marque uma issue como `done` se a entrega depende de alteração em arquivo
e essa alteração ainda aparece apenas em `git diff` ou `git status`.

Se o board, o usuário ou outro agente não consegue ver a alteração no commit,
branch, PR ou `main`, a entrega não existe para o projeto.

## Definição de Pronto

Para mudanças em código, documentação, configuração, scripts, assets ou skills
versionados, a issue só pode ser encerrada quando houver:

1. diff conferido e limitado ao escopo da issue;
2. commit criado com mensagem específica;
3. branch publicada no remoto, quando a alteração não for commit direto permitido;
4. PR aberto ou atualizado, quando o fluxo do projeto exigir PR;
5. PR mergeado ou issue deixada em `in_review` com caminho real de revisão;
6. comentário final da issue com evidência verificável.

Editar localmente e comentar "feito" é falha de execução.

## Procedimento Obrigatório

### 1. Antes de editar

Verifique o estado do repositório:

```bash
git status --short --branch
```

Se houver mudanças não relacionadas:

- não reverta;
- não misture;
- não faça commit amplo;
- use uma branch/worktree limpa quando necessário.

Se a branch atual pertencer a outra issue, estiver divergente ou tiver histórico
inadequado, crie uma worktree limpa a partir da base correta:

```bash
git fetch origin main --prune
git worktree add /tmp/<issue>-worktree origin/main -b <issue>-slug
```

### 2. Depois de editar

Confira exatamente o que será entregue:

```bash
git diff -- <arquivos>
git diff --check
git status --short
```

Para documentação, confira também links e caminhos citados. Não publique README
com link para arquivo que não existe na branch de destino.

### 3. Antes do commit

Coloque no staging apenas o escopo da issue:

```bash
git add <arquivos-da-issue>
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Se aparecer arquivo que não pertence à issue, remova do staging antes de
continuar.

### 4. Commit e publicação

Crie commit específico:

```bash
git commit -m "<tipo>: <descrição objetiva>"
```

Publique a branch:

```bash
git push -u origin <branch>
```

Abra ou atualize PR quando o trabalho não puder ser integrado diretamente:

```bash
gh pr create --base main --head <branch> --title "<título>" --body "<resumo>"
```

### 5. Merge ou revisão

Se o PR estiver limpo, sem aprovação humana pendente e sem checks obrigatórios
falhando, o agente responsável deve concluir o fluxo técnico até o merge quando
tiver permissão para isso.

Se houver bloqueio real, a issue não deve ficar `done`. Use:

- `in_review` quando houver PR, aprovação ou revisão real pendente;
- `blocked` quando existir bloqueio concreto com dono e ação de desbloqueio;
- subtarefa filha quando outro agente for responsável pela próxima ação.

## Comentário Final Obrigatório

O comentário final da issue deve incluir:

- arquivos alterados;
- commit hash;
- branch;
- PR, se houver;
- merge commit, se houver;
- checks executados ou motivo de não aplicação;
- estado final: `done`, `in_review` ou `blocked`;
- declaração explícita sobre TDD e skills obrigatórios quando a tarefa envolver
  código, bugfix, refactor, CI técnico ou revisão de código.

Exemplo mínimo:

```markdown
Status: done

- Arquivos: `README.md`
- Commit: `0aba9c1`
- PR: #27
- Merge em main: `7be2d31`
- Verificação: `git diff --check`; links locais conferidos
- TDD: não aplicável, alteração documental sem mudança de comportamento
```

## Proibições

- Não marque `done` com arquivo modificado e não commitado.
- Não diga "feito" usando apenas evidência de diff local.
- Não commite mudanças de outros agentes para "limpar" o workspace.
- Não publique branch divergente de outra issue como se fosse entrega atual.
- Não abra PR com arquivos fora do escopo.
- Não deixe PR aberto sem colocar a issue em `in_review`, `blocked` ou sem
  caminho real de continuidade.
- Não esconda falha de CI em comentário otimista. Falha de CI é trabalho
  pendente, não detalhe administrativo.

## Exceções

Só é aceitável encerrar sem commit quando a tarefa não produz alteração
versionável, por exemplo:

- triagem sem mudança de arquivo;
- resposta técnica na issue;
- decisão arquitetural registrada em comentário;
- investigação que conclui "nenhuma alteração necessária".

Mesmo nesses casos, o comentário final deve dizer explicitamente que não houve
arquivo alterado e por quê.
