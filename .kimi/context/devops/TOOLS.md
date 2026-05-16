# TOOLS — DevOps Engineer

## `Think`
Use antes de qualquer mudança de infra. Raciocine sobre:
- A mudança afeta produção? (→ confirmação humana obrigatória)
- Há segredos envolvidos? Como serão gerenciados?
- Qual o procedimento de rollback?
- Há dependências externas (actions, imagens) sem pin de versão?
- A mudança é reversível? (guardrail Karpathy #3)

---

## `ReadFile`
Leia sempre antes de modificar:
- O arquivo de pipeline existente (.github/workflows/, .gitlab-ci.yml)
- Dockerfile e docker-compose.yml
- Arquivos de IaC (terraform/, pulumi/)
- README de deploy e documentação de infra existente
- Scripts de deploy e makefile

---

## `Glob`
Use para mapear a infra existente:
```
.github/workflows/**       → todos os pipelines GitHub Actions
.gitlab-ci.yml             → pipeline GitLab CI
Dockerfile*                → todos os Dockerfiles
docker-compose*.yml        → todos os compose files
terraform/**/*.tf          → todos os arquivos Terraform
**/k8s/**                  → manifestos Kubernetes
scripts/**                 → scripts de deploy e automação
```

---

## `Grep`
Use para auditar segurança e dependências:
```
"password\|secret\|token\|key\|api_key"  → segredos potenciais em código
"uses:"                                   → actions GitHub em uso
"image:"                                  → imagens Docker em uso
"latest"                                  → tags não pinadas
"\$\{\{"                                  → variáveis de secrets no pipeline
```

---

## `Shell`
Use para:
- Validar sintaxe de pipeline: `act --list` (GitHub), `gitlab-ci-lint`
- Lint de Dockerfile: `hadolint Dockerfile`
- Validar Terraform: `terraform validate`, `terraform plan`
- Verificar YAML: `yamllint .github/workflows/`
- Testar scripts localmente antes de commitar

**Para execução em produção: sempre reporte ao CEO primeiro.**

---

## `WriteFile` / `StrReplaceFile`
WriteFile para criar novos arquivos de pipeline, Dockerfile, compose.
StrReplaceFile para edições cirúrgicas em pipelines existentes.

**Preferir StrReplaceFile para pipelines existentes — menos risco
de introduzir erro por reescrita completa.**

---

## `SearchWeb` / `FetchURL`
Use para:
- Documentação oficial GitHub Actions / GitLab CI
- Últimas versões seguras de actions (para pin por hash)
- Buscar hashes SHA de actions: `https://github.com/<owner>/<repo>/releases`
- Melhores práticas de segurança de pipeline (OWASP, SLSA)
- Documentação de serviços cloud (AWS, GCP, Azure)
