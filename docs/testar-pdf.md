# Script CLI `testar_pdf.py`

Extrai dados de sentença (sucumbente, valor, honorários) a partir de um PDF judicial.

## Instalação

```bash
pip install -r agente/requirements.txt   # instala pymupdf e dependências
```

## Uso básico

```bash
python agente/scripts/testar_pdf.py \
  docs/processos/0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf
```

## Flags

| Flag | Descrição |
|------|-----------|
| `--verbose` | Mostra o texto bruto extraído do PDF (primeiros 4000 caracteres) |
| `--llm` | Força extração via LLM em vez de regex (requer `OPENAI_API_KEY`) |
| `--area civel\|trabalhista` | Área do direito (padrão: `civel`) |

## Interpretação do resultado

| Campo | Significado |
|-------|-------------|
| **Sucumbente** | Nome da parte condenada (quem perdeu a ação) |
| **Tipo** | `autor`, `réu` ou `reclamada` |
| **Valor Condenação** | Valor monetário da condenação principal |
| **Honorários %** | Percentual de honorários de sucumbência |
| **Suspensão (art. 98 §3º)** | `Sim` se gratuidade de justiça foi deferida |
| **Método** | `regex` ou `llm` — qual estratégia extraiu os dados |
| **Score** | 0.00 a 1.00 — proporção dos 3 campos obrigatórios preenchidos |

O script também imprime dois blocos JSON: o resultado da sentença e o resultado do parser de documentos.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| `0` | Sucesso |
| `1` | Erro (PDF inválido, texto ilegível ou falha no parser) |
| `2` | PDF scanned (sem texto selecionável) — OCR não implementado |

## Limitações

- PDFs scanned (apenas imagem) não são suportados; o script encerra com código `2`.
- A extração via LLM depende da variável de ambiente `OPENAI_API_KEY`.
