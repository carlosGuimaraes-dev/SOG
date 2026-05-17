# Script CLI `testar_pdf.py`

Extrai dados de sentença (sucumbente, valor, honorários) e custas iniciais a partir de um PDF judicial.

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
| **Custas Iniciais** | Valor total e detalhamento da guia de pagamento (quando presente no PDF) |

O script imprime três blocos JSON: o resultado da sentença, o resultado das custas iniciais e o resultado do parser de documentos.

## JSON de custas iniciais

Quando o PDF contém uma guia de pagamento de custas, o extrator localiza o documento pelo `doc_id` da capa do processo, isola a região da guia no texto completo e extrai:

```json
{
  "encontrado": true,
  "scanned": false,
  "valor_total": "266,95",
  "valor_total_centavos": 26695,
  "detalhamento": {
    "distribuidor": "10,74",
    "mandados": "8,83",
    "oficios": "8,83",
    "contador": "13,21",
    "custas": "203,16",
    "diligencias": "22,18"
  },
  "numero_guia": "001-9",
  "vencimento": "11/08/2024",
  "doc_id": "206426308"
}
```

Se a guia não for encontrada, o campo retorna `{"encontrado": false, "scanned": false}`. Se o PDF for scanned (imagem), retorna `{"encontrado": false, "scanned": true}`.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| `0` | Sucesso |
| `1` | Erro (PDF inválido, texto ilegível ou falha no parser) |
| `2` | PDF scanned (sem texto selecionável) — OCR não implementado |

## Limitações

- PDFs scanned (apenas imagem) não são suportados; o script encerra com código `2`.
- A detecção de PDFs scanned usa uma **heurística agregada**: o arquivo só é considerado scanned se **≥80% das páginas** forem image-only (menos de 30 caracteres de texto + presença de imagem) **e** a média de texto por página for **inferior a 100 caracteres**. Isso evita falsos positivos em PDFs cuja capa é predominantemente imagem, mas cujo conteúdo principal contém texto selecionável.
- A extração via LLM depende da variável de ambiente `OPENAI_API_KEY`.
