---
name: technical-documentation
description: Use ao criar, revisar ou manter documentação técnica do projeto. Aplica-se a READMEs, changelogs, docstrings, comentários de código e guias de desenvolvimento.
---

# Documentação Técnica

## Resumo

Documentação técnica viva é um ativo, não overhead. Ela reduz tempo de onboarding, prevenção de erros repetidos e decisões baseadas em conhecimento tribal. O princípio fundamental: documente o **porquê**, não o **quê** — o código já diz o que faz.

## Quando usar

- Ao criar ou atualizar um módulo, serviço ou API
- Durante onboarding de novos desenvolvedores
- Ao identificar bugs causados por mal-entendidos do sistema
- Após mudanças arquiteturais significativas
- Quando uma pergunta é feita mais de uma vez (sinal de documentação ausente)

## Padrões principais

### README

Cada projeto e módulo significativo deve ter um README com:

1. **Propósito** — uma frase do que faz e para quem
2. **Pré-requisitos** — versões de linguagem, dependências, variáveis de ambiente
3. **Instalação** — comandos copiáveis e coláveis
4. **Execução** — como rodar localmente e em produção
5. **Estrutura** — mapa de diretórios principais
6. **Testes** — como executar
7. **Contribuição** — link para guia ou regras básicas

```markdown
# Agente de Coleta de Custas

Extrai custas processuais do TJDFT via automação Playwright.

## Pré-requisitos
- Python 3.11+
- Playwright instalado: `playwright install chromium`

## Execução local
```bash
pip install -r requirements.txt
python src/main.py
```

## Variáveis de ambiente
Ver `src/config.py` para lista completa.
```

### CHANGELOG

Siga [Keep a Changelog](https://keepachangelog.com/) com [Semantic Versioning](https://semver.org/):

- `Added` — novas features
- `Changed` — alterações em funcionalidades existentes
- `Deprecated` — funcionalidades que serão removidas
- `Removed` — funcionalidades removidas
- `Fixed` — correções de bugs
- `Security` — vulnerabilidades corrigidas

```markdown
## [1.2.0] - 2026-05-10

### Added
- Suporte a múltiplos números de processo por execução

### Fixed
- Timeout em páginas com carregamento lento de JS
```

### Docstrings

Use docstrings para funções e classes públicas. Formato mínimo:

```python
def extrair_custas(html: str) -> list[dict]:
    """Extrai linhas de custas de uma página HTML do PJe.

    Args:
        html: Conteúdo HTML da página de custas.

    Returns:
        Lista de dicionários com chaves: descricao, valor, data.

    Raises:
        ValueError: Se o HTML não contiver a tabela esperada.
    """
```

Regras:
- Documente parâmetros, retorno e exceções
- Inclua exemplo se a função tiver comportamento não-obvio
- Mantenha em 3-10 linhas; funções complexas precisam de refatoração, não docstring maior

### Comentários inline

Comente **porquê**, nunca **quê**:

```python
# Ruim: o que o código faz
x = x + 1  # incrementa x

# Bom: por que faz
x = x + 1  # compensa índice base-0 do PJe que retorna base-1
```

Use comentários para:
- Workarounds de bugs de terceiros (com link para issue)
- Decisões não-obvias de performance
- Restrições de negócio que não estão no tipo

Não use para:
- Explicar sintaxe da linguagem
- Documentar o óbvio (`# cria a lista` antes de `lista = []`)

### Documentação de decisões

Decisões não-obvias vão em ADRs (ver skill `architecture-decisions`) ou em seção dedicada do README. Não deixe decisões importantes apenas em comentários de código.

### Exemplos de código executáveis

Todo exemplo de documentação deve ser:

1. **Copiável e colável** — funciona sem modificação
2. **Testado** — parte da suite de testes ou verificado manualmente a cada release
3. **Completo** — inclui imports e setup necessário

```python
# README.md — exemplo de uso da API
import httpx

response = httpx.post(
    "http://api.localhost/custas",
    json={"numero_processo": "0001234-12.2024.8.07.0012"},
    headers={"Authorization": "Bearer <token>"}
)
print(response.json()["total"])
```

### Manutenção da documentação

- Reveja README a cada release
- Atualize docstrings quando mudar assinaturas
- Trate exemplos quebrados como bugs — abra issue
- Remova documentação obsoleta; informação errada é pior que ausente
- Use `markdownlint` ou similar para consistência de formatação

## Exemplos

### Docstring de classe com exemplo

```python
class AgenteCustas:
    """Orquestra extração de custas do TJDFT.

    Gerencia o ciclo de vida do browser, login e extração
    de dados para um ou mais números de processo.

    Example:
        >>> agente = AgenteCustas(headless=True)
        >>> custas = agente.extrair("0001234-12.2024.8.07.0012")
        >>> print(custas[0]["total"])
        1250.0
    """
```

### Comentário de workaround

```python
# PJe renderiza a tabela via JS após um delay variável.
# Playwright's auto-wait não detecta esse elemento específico.
# Workaround: espera explícita de 2s após networkidle.
# Ref: https://github.com/microsoft/playwright/issues/12345
page.wait_for_timeout(2000)
```

## Anti-patterns

- **README desatualizado** — instruções de instalação que não funcionam
- **Docstrings óbvias** — `"""Retorna x."""` para `def get_x(self):`
- **Comentários explicando sintaxe** — `# loop for` antes de um `for`
- **Exemplos quebrados** — código copiado que não compila ou executa
- **Documentação duplicada** — mesma informação em README e wiki; uma fonte de verdade
- **Sem CHANGELOG** — histórico de mudanças só no git log, ilegível para usuários
