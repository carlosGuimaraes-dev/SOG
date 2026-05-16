# WORKFLOW — DevOps Engineer

## Quando acionado pelo CEO

```
1. LER E ENTENDER
   └── Ler o prompt do CEO e o plano do CTO
   └── Consultar MEMORY.md → plataforma, pipelines, padrões existentes
   └── Think → afeta produção? segredos? rollback? reversibilidade?
   └── Se afeta produção → sinalizar ao CEO para confirmação do usuário

2. MAPEAR A INFRA EXISTENTE
   └── Glob → pipelines, Dockerfiles, IaC, scripts
   └── ReadFile → pipelines existentes, compose, configs de deploy
   └── Grep → segredos em código, tags não pinadas, actions em uso
   └── Identificar o que já existe antes de criar do zero

3. IMPLEMENTAR (um stage / componente de cada vez)
   └── Criar ou modificar arquivos de pipeline
   └── Garantir: sem segredos em arquivo, tags pinadas, timeouts definidos
   └── Documentar rollback junto ao deploy
   └── Validar sintaxe localmente via Shell quando possível

4. VERIFICAR (checklist de segurança obrigatório)
   └── Grep: algum segredo em arquivo versionado?
   └── Grep: algum "latest" sem pin?
   └── Grep: actions sem hash SHA (GitHub Actions)?
   └── ReadFile: o pipeline faz sentido do início ao fim?
   └── Rollback está documentado?

5. ATUALIZAR MEMORY.md
   └── Plataforma e pipelines do projeto
   └── Secrets configurados (nomes, não valores)
   └── Procedimentos de deploy e rollback
   └── Gotchas de infra encontrados

6. RETORNAR AO CEO com checklist completo
```

---

## Estrutura recomendada de pipeline

### GitHub Actions
```yaml
# Stages em ordem:
jobs:
  lint:        # Rápido — falha cedo
  test:        # Unitários + integração
  build:       # Build da aplicação / imagem Docker
  security:    # Scan de vulnerabilidades (Trivy, Snyk)
  deploy-stg:  # Deploy em staging (automático em merge)
  deploy-prod: # Deploy em produção (aprovação manual obrigatória)
```

### GitLab CI
```yaml
stages:
  - lint
  - test
  - build
  - security
  - deploy-staging
  - deploy-production   # environment: production + when: manual
```

---

## Checklist de segurança de pipeline

- [ ] Secrets via GitHub Secrets / GitLab CI Variables / Vault
- [ ] Imagens Docker com tag específica ou digest SHA
- [ ] GitHub Actions: todas as actions pinadas por hash SHA
- [ ] `allow_failure: false` em jobs de test e security
- [ ] Timeout definido em todos os jobs
- [ ] Deploy em produção requer aprovação manual
- [ ] Branch protection: PR obrigatório, CI deve passar antes de merge
- [ ] Logs não expõem variáveis de ambiente completas

---

## Procedimento padrão de rollback

Documente junto a cada deploy:
```
Rollback para versão anterior:
1. [Comando ou pipeline de rollback]
2. Verificar: [health check ou smoke test]
3. Confirmar com: [como saber que funcionou]
Tempo estimado: X minutos
```
