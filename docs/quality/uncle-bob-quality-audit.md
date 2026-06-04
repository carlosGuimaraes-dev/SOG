# 🔍 Uncle Bob Quality Audit Report

| Campo | Valor |
|---|---|
| **Linguagem detectada** | Python + TypeScript/TSX + JavaScript/Node.js |
| **Arquivos analisados** | 177 arquivos fonte: 81 Python, 80 TypeScript/TSX, 16 JavaScript; excluídos `.git/`, `.kimi/`, `node_modules/`, caches, builds e `dados/` |
| **Tipo de análise** | Estática (sem execução de código) |
| **Versão da skill** | uncle-bob-quality v3.0.0 |

> ⚠️ Esta análise é estática. Métricas como cobertura real e mutation score
> requerem execução das ferramentas de CI geradas no Passo 5.

---

## Score Geral

| Dimensão | Score | Resumo em uma frase |
|---|---|---|
| Test Coverage | 🟡 AMARELO | Há 50 arquivos de teste com asserts específicos, mas não havia workflow de CI medindo coverage mínimo de 80%. |
| Dependency Structure | 🟢 VERDE | A varredura estática não encontrou ciclos de import internos detectáveis e o frontend concentra acesso HTTP em hooks/libs. |
| Cyclomatic Complexity | 🔴 VERMELHO | Há funções/componentes com complexidade estimada muito acima do limite, chegando a 56. |
| Module Sizes | 🔴 VERMELHO | Há funções acima de 20 linhas e arquivos acima de 500 linhas, acionando reprovação imediata. |
| Mutation Readiness | 🟡 AMARELO | Existem asserts fortes, mas não havia mutation testing automatizado nem score real disponível. |

**Veredicto:**
- Qualquer VERMELHO → `❌ REPROVADO`

---

## 1. Test Coverage

**Score:** 🟡

**Critério aplicado:**
- VERDE: lógica de negócio coberta + casos de borda + asserts específicos
- AMARELO: cobertura parcial, apenas caminho feliz
- VERMELHO: zero testes, testes sem assert, ou smoke tests apenas

**O que foi encontrado:**
Foram detectados 50 arquivos de teste em `frontend/src/**`, `api/tests/**` e `agente/tests/**`. Há asserts específicos em testes de regra, DataJud, CSS escaping e componentes React, mas os workflows existentes eram voltados a desktop/release/imagens e não rodavam coverage como gate de qualidade.

**Problemas encontrados:**
- Coverage não era gate de CI | Localização: `.github/workflows/` | Evidência: `sog-desktop-windows.yml`, `sog-desktop-r2-release.yml`, `sog-desktop-images.yml` sem `pytest --cov` ou `vitest --coverage`
- Setup/fixtures sem assert, aceitável como suporte mas não como cobertura de comportamento | Localização: `frontend/src/__tests__/setupTests.ts`, `api/tests/conftest.py`, `agente/tests/conftest.py` | Evidência: `assertCount: 0`

**Recomendações:**
- Manter testes existentes e passar a exigir coverage mínimo de 80% em CI para Python e frontend.
- Separar fixtures/configuração de testes da métrica de cobertura comportamental.

---

## 2. Dependency Structure

**Score:** 🟢

**Critério aplicado:**
- VERDE: fluxo unidirecional, sem ciclos, interfaces bem definidas
- AMARELO: dependências transversais sem ciclos
- VERMELHO: ciclos detectados, God objects, UI acoplada a persistência

**O que foi encontrado:**
A análise de imports Python internos detectou 1 aresta interna e nenhum ciclo. No frontend, o acesso a dados aparece concentrado em `frontend/src/hooks/useProcesso.ts`, `frontend/src/lib/api.ts` e `frontend/src/lib/endpoints.ts`, sem persistência direta generalizada em componentes.

**Problemas encontrados:**
- Nenhum problema detectável estaticamente.

**Recomendações:**
- Adotar verificação automatizada de dependências no CI para impedir ciclos futuros em `frontend/src`.

---

## 3. Cyclomatic Complexity

**Score:** 🔴

**Critério aplicado:**
- VERDE: complexidade ≤ 10 em todas as funções
- AMARELO: complexidade 11–15 em alguma função
- VERMELHO: complexidade > 15 em alguma função

**Funções analisadas:**

| Função | Pontos de decisão contados | Complexidade estimada | Status |
|---|---|---|---|
| `frontend/src/pages/CicloAtual.tsx:274 CicloAtual()` | decisões=55 | 56 | 🔴 |
| `frontend/src/pages/Fila.tsx:133 Fila()` | decisões=29 | 30 | 🔴 |
| `agente/src/modulos/extrator_sentenca.py:99 extrair_sentenca_regex()` | decisões=26 | 27 | 🔴 |
| `agente/src/modulos/sistjweb.py:274 preencher()` | decisões=24 | 25 | 🔴 |
| `desktop/renderer/app.js:44 refresh()` | decisões=23 | 24 | 🔴 |
| `frontend/src/pages/Detalhe.tsx:27 Detalhe()` | decisões=20 | 21 | 🔴 |
| `shared/sog_shared/agente_ciclos.py:431 fechar_snapshot_ciclo()` | decisões=11 | 12 | 🟡 |

**Recomendações:**
- Extrair estado e renderização condicional de `CicloAtual()` e `Fila()` para hooks/componentes menores.
- Quebrar `extrair_sentenca_regex()` em extratores nomeados por campo.
- Separar navegação/preenchimento/extração de resultado em `SISTJWeb.preencher()`.

---

## 4. Module Sizes

**Score:** 🔴

**Critério aplicado:**
- VERDE: funções ≤ 20 linhas, classes ≤ 200 linhas, arquivos ≤ 500 linhas
- AMARELO: alguma unidade até 30% acima do limite
- VERMELHO: qualquer unidade > 30% acima do limite

**Inventário:**

| Unidade | Tipo | Linhas contadas | Limite | Status |
|---|---|---|---|---|
| `frontend/src/pages/Fila.tsx:133 Fila()` | função | 181 | 20 | 🔴 |
| `frontend/src/pages/CicloAtual.tsx:274 CicloAtual()` | função | 173 | 20 | 🔴 |
| `agente/src/modulos/sistjweb.py:274 preencher()` | função | 170 | 20 | 🔴 |
| `agente/src/modulos/pje.py:388 coletar_documentos()` | função | 126 | 20 | 🔴 |
| `agente/src/modulos/extrator_sentenca.py:99 extrair_sentenca_regex()` | função | 116 | 20 | 🔴 |
| `shared/sog_shared/agente_ciclos.py` | arquivo | 538 | 500 | 🟡 |
| `agente/src/servico.py` | arquivo | 503 | 500 | 🟡 |

**Recomendações:**
- Extrair funções puras de transformação antes de mexer em I/O e Playwright.
- Priorizar `CicloAtual()`, `Fila()` e `preencher()` porque combinam tamanho alto e complexidade alta.

---

## 5. Mutation Readiness (Inferida)

**Score:** 🟡

**Critério aplicado:**
- VERDE: asserts com valores específicos, mocks verificados com argumentos, casos de borda cobertos
- AMARELO: mix de asserts fortes e fracos
- VERMELHO: asserts genéricos, sem verificação de valores, testes que não detectariam retorno errado

> ⚠️ Esta dimensão é **inferida estaticamente**. O score real só é obtido
> executando as ferramentas de mutation testing geradas no CI (Stryker/mutmut/cargo-mutants).

**Testes provavelmente frágeis a mutantes:**
- `frontend/src/__tests__/setupTests.ts` | Motivo: arquivo de setup não contém assert comportamental | Evidência: `assertCount: 0`
- `api/tests/conftest.py` | Motivo: fixture de suporte não mata mutantes por si só | Evidência: `assertCount: 0`
- `agente/tests/conftest.py` | Motivo: fixture de suporte não mata mutantes por si só | Evidência: `assertCount: 0`

**Testes provavelmente robustos:**
- `agente/tests/test_datajud.py` | Motivo: valida valores específicos de retorno, por exemplo classe processual.
- `agente/tests/test_css_escape.py` | Motivo: valida transformação exata de entrada para saída.
- `frontend/src/components/fila/BuscaProcesso.test.tsx` | Motivo: usa `expect` em comportamento de componente.

**Recomendações:**
- Rodar mutation testing em `workflow_dispatch` e `schedule`, não em todo PR inicialmente.
- Promover mutantes sobreviventes a testes unitários específicos antes de refatorar módulos grandes.

---

## Action Items Priorizados

### 🔴 Crítico — resolver antes de qualquer merge
1. Reduzir `frontend/src/pages/CicloAtual.tsx:274 CicloAtual()` para unidades menores | Métrica: Cyclomatic Complexity / Module Sizes | Esforço estimado: alto
2. Reduzir `frontend/src/pages/Fila.tsx:133 Fila()` para unidades menores | Métrica: Cyclomatic Complexity / Module Sizes | Esforço estimado: alto
3. Quebrar `agente/src/modulos/sistjweb.py:274 preencher()` em etapas testáveis | Métrica: Cyclomatic Complexity / Module Sizes | Esforço estimado: alto
4. Quebrar `agente/src/modulos/extrator_sentenca.py:99 extrair_sentenca_regex()` por responsabilidade de extração | Métrica: Cyclomatic Complexity / Module Sizes | Esforço estimado: médio

### 🟡 Importante — resolver neste sprint
1. Acompanhar `shared/sog_shared/agente_ciclos.py` e `agente/src/servico.py`, ambos acima de 500 linhas | Métrica: Module Sizes | Esforço estimado: médio
2. Transformar coverage mínimo de 80% em gate obrigatório no CI | Métrica: Test Coverage | Esforço estimado: baixo
3. Adicionar verificação automatizada de dependências do frontend | Métrica: Dependency Structure | Esforço estimado: baixo

### 🟢 Melhoria — backlog técnico
1. Rodar mutation testing semanal e abrir issues para mutantes sobreviventes | Métrica: Mutation Readiness | Esforço estimado: médio
2. Registrar baseline de complexidade após as primeiras extrações | Métrica: Cyclomatic Complexity | Esforço estimado: baixo

---
*Relatório gerado pela skill uncle-bob-quality v3.0.0 — llm-agnostic*
