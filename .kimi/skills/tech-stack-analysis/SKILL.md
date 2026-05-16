---
name: tech-stack-analysis
description: Use ao avaliar, comparar ou selecionar tecnologias, bibliotecas, frameworks, ferramentas ou serviços para o projeto. Aplica-se a escolhas de frontend, backend, banco de dados, infraestrutura e ferramentas de desenvolvimento.
---

# Análise e Seleção de Stack Tecnológica

## Resumo

A escolha de tecnologia deve ser deliberada, não baseada em hype ou familiaridade individual. Uma análise rigorosa avalia maturidade, curva de aprendizado, compatibilidade com stack existente e riscos — resultando em uma recomendação documentada e, quando possível, validada por uma POC mínima.

## Quando usar

- Ao iniciar um novo projeto ou módulo
- Ao substituir uma biblioteca ou serviço existente
- Quando uma dependência atual apresenta riscos (manutenção, licença, segurança)
- Ao escalar o time e precisar de tecnologias com curva de aprendizado adequada
- Quando stakeholders questionam uma escolha tecnológica

## Padrões principais

### Critérios de avaliação

Avalie candidatos em pelo menos estas dimensões:

| Critério | O que verificar | Fontes |
|----------|-----------------|--------|
| Maturidade | Versão estável, tempo de existência, adotantes conhecidos | GitHub releases, who uses, case studies |
| Comunidade | Tamanho, atividade, tempo médio de resposta a issues | GitHub insights, Stack Overflow, Discord |
| Curva de aprendizado | Tempo para produtividade básica, familiaridade do time | Protótipo de 2-4 horas |
| Documentação | Completa, atualizada, com exemplos | Site oficial, README, changelogs |
| Performance | Benchmarks relevantes ao caso de uso | Testes próprios, benchmarks públicos |
| Licença | Compatível com uso comercial | SPDX, OSI |
| Manutenção | Frequência de releases, número de maintainers | GitHub activity, bus Factor |

Use uma matriz de pontuação simples (1-5) para comparar candidatos. Não use pesos sem justificar por quê.

### POC mínima

Antes de decidir, construa uma prova de conceito que exercite o caminho crítico:

1. **Escopo de 1-2 dias** — não 1 semana
2. **Caminho feliz + 1 erro** — valide não apenas o sucesso
3. **Integração real** — teste com a stack existente, não isoladamente
4. **Critério de aceite binário** — "POC passa se X conseguir Y em Z segundos"

Exemplo de critério:

```markdown
POC Playwright:
- Fazer login no PJe
- Extrair número do processo
- Executar em headless em < 30s
- Se falhar em 3 tentativas consecutivas, descartar
```

### Análise de riscos

Para cada candidato, identifique:

- **Risco técnico** — limitações conhecidas, bugs críticos abertos
- **Risco de manutenção** — bus factor, frequência de releases, roadmap claro
- **Risco de adoção** — curva de aprendizado do time, disponibilidade de contratação
- **Risco de vendor lock-in** — dificuldade de migração, custo de saída

Documente mitigações: "Se a biblioteca for abandonada, ponto de substituição é a interface X".

### Compatibilidade com stack existente

Verifique explicitamente:

- Versionamento de linguagem compatível
- Conflitos de dependências transitivas (`pip install` ou `npm ls`)
- Paradigma de programação alinhado (async vs sync, OOP vs funcional)
- Formato de dados e protocolos de comunicação
- Infraestrutura necessária (Docker, serviços externos, portas)

### Custos

Considere todos os custos, não apenas licença:

- **Diretos** — licenças, hospedagem, serviços externos
- **Indiretos** — tempo de aprendizado, onboarding, manutenção
- **Oportunidade** — tempo não gasto em outras features

Compare TCO (total cost of ownership) em 1 ano, não apenas custo inicial.

### Documentação da recomendação

A recomendação final deve conter:

1. **Resumo executivo** — decisão em uma frase
2. **Candidatos avaliados** — tabela comparativa
3. **Recomendação** — qual e por quê
4. **POC** — resultado e critério de pass/fail
5. **Riscos e mitigações** — principais preocupações
6. **Plano de rollback** — como reverter se necessário

## Exemplos

### Análise de biblioteca de parsing de PDF

```markdown
## Candidatos

| Critério | PyPDF2 | pdfplumber | pypdf |
|----------|--------|------------|-------|
| Maturidade | 3 | 4 | 4 |
| Comunidade | 3 | 4 | 4 |
| Extração de tabelas | 2 | 5 | 2 |
| Performance | 4 | 3 | 4 |
| Licença | BSD | MIT | BSD |

## Recomendação
pdfplumber — extração de tabelas é requisito crítico e não há
substituto viável nos outros candidatos. Risco de performance
será mitigado com cache de 24h.

## POC
Script extraíu 47 tabelas de 50 PDFs de teste em < 2s cada.
Falhou em 3 casos de células mescladas — aceitável para MVP.
```

### Matriz de decisão com pesos justificados

```markdown
Critérios e pesos:
- Performance: 30% (requisito não-funcional SLA < 2s)
- Manutenção: 25% (time pequeno, bus factor crítico)
- Curva de aprendizado: 20% (novos devs a cada 3 meses)
- Comunidade: 15%
- Licença: 10%

Pesos definidos com time em sessão de 15 min. Documentado em ADR-009.
```

## Anti-patterns

- **Decisão por hype** — "Todo mundo está usando" não é critério
- **Análise sem POC** — comparar documentação não substitui experimentação
- **Ignorar stack existente** — adicionar tecnologia que conflita com infraestrutura atual
- **Custos esquecidos** — considerar apenas licença, ignorar aprendizado e manutenção
- **Recomendação sem alternativas** — sempre documente pelo menos 2 candidatos
- **Matriz sem justificativa de pesos** — pesos arbitrários mascaram viés pessoal
