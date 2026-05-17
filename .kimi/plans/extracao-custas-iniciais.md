# Plano Técnico — Extração de Valor das Custas Iniciais de PDF

> **Tarefa:** Adicionar extração de valor das custas iniciais ao módulo `agente/src/modulos/extrator_pdf.py`
> **Data:** 2026-05-17
> **Status:** Aprovado para execução

---

## Visão geral da solução

Adicionar uma função `extrair_custas_iniciais()` que reusa os dados já extraídos por `extrair_texto_pdf()` e `extrair_documentos_capa()`. A nova função identifica documentos do tipo "Guia" ou "Comprovante de Pagamento de Custas" na capa, localiza a ocorrência do `doc_id` no texto completo do PDF para isolar a região da guia, e aplica regex robustos para extrair o valor total, detalhamento por item, número da guia e vencimento. O resultado é integrado ao dict de retorno de `extrair_texto_pdf()` sob a chave `"custas_iniciais"`, e o CLI `testar_pdf.py` passa a exibir esse dado.

---

## Arquivos a criar / modificar / deletar

| Ação | Caminho |
|------|---------|
| **Modificar** | `agente/src/modulos/extrator_pdf.py` |
| **Modificar** | `agente/tests/test_extrator_pdf.py` |
| **Modificar** | `agente/scripts/testar_pdf.py` |
| **Modificar** | `.kimi/context/cto/MEMORY.md` (registro de decisão) |

---

## Interfaces e contratos

### Nova função pública

```python
def extrair_custas_iniciais(caminho: str) -> Dict[str, Any]:
    """Extrai valor das custas iniciais a partir de guias de pagamento no PDF.

    Recebe caminho do PDF, identifica documentos do tipo "Guia" ou
    "Comprovante de Pagamento de Custas" na capa, localiza o conteúdo
    da guia no texto completo e extrai valores monetários.

    Retorna:
        {
            "encontrado": True,
            "valor_total": "266,95",           # string com formato brasileiro
            "valor_total_centavos": 26695,     # int para cálculos
            "detalhamento": {
                "distribuidor": "10,74",
                "mandados": "8,83",
                "oficios": "8,83",
                "contador": "13,21",
                "custas": "203,16",
                "diligencias": "22,18",
            },
            "doc_id": "206426308",
            "numero_guia": "001-9",
            "vencimento": "11/08/2024",
            "scanned": False,
        }

    Ou, quando não encontrado:
        {"encontrado": False, "scanned": bool}

    Quando o PDF é scanned (sem texto selecionável):
        {"encontrado": False, "scanned": True}
    """
```

### Função auxiliar interna

```python
def _extrair_valor_guia(texto_regiao: str) -> Optional[Dict[str, Any]]:
    """Aplica regex em uma região de texto para extrair dados da guia.

    Retorna dict com os campos da guia se encontrar padrões reconhecidos,
    ou None se a região não contiver dados de guia.
    """
```

### Modificação no retorno de `extrair_texto_pdf()`

O dict retornado passa a incluir a chave aditiva:

```python
"custas_iniciais": {
    "encontrado": True | False,
    # ... campos conforme contrato acima
}
```

### Função utilitária (reuso)

```python
def _parse_valor_monetario(texto: str) -> Tuple[str, int]:
    """Converte string como 'R$ 1.234,56' ou '1234,56' em (str_formatada, centavos_int).

    Retorna ("1234,56", 123456). Se inválido, ("", 0).
    """
```

---

## Regex especificados

### Valor total (múltiplos padrões, ordem de prioridade)

```python
_RE_VALOR_TOTAL = re.compile(
    r'(?:valor\s+total)[:\s]*R?\$?\s*([\d\.]+,\d{2})',
    re.IGNORECASE,
)
```

Fallback mais permissivo:
```python
_RE_VALOR_TOTAL_LOOSE = re.compile(
    r'R?\$\s*([\d\.]+,\d{2})',
    re.IGNORECASE,
)
```

> **Nota:** O regex prioritário deve ser aplicado primeiro. O fallback só é usado quando o prioritário falha, e deve ser combinado com contexto de guia (próximo a "Número da Guia", "Vencimento", etc.) para evitar false positives.

### Detalhamento por item

```python
_RE_DETALHAMENTO = {
    "distribuidor": re.compile(r'(?:distribuidor|distribui[cç][aã]o)[:\s]+([\d\.]+,\d{2})', re.I),
    "mandados": re.compile(r'(?:mandados?)[:\s]+([\d\.]+,\d{2})', re.I),
    "oficios": re.compile(r'(?:of[ií]cios?)[:\s]+([\d\.]+,\d{2})', re.I),
    "contador": re.compile(r'(?:contador)[:\s]+([\d\.]+,\d{2})', re.I),
    "custas": re.compile(r'(?:custas?)[:\s]+([\d\.]+,\d{2})', re.I),
    "diligencias": re.compile(r'(?:dilig[eê]ncias?)[:\s]+([\d\.]+,\d{2})', re.I),
}
```

### Número da guia

```python
_RE_NUMERO_GUIA = re.compile(
    r'(?:n[uú]mero\s+(?:da\s+)?guia|guia\s+n[º°o]?)[:\s]+(\S+)',
    re.IGNORECASE,
)
```

### Vencimento

```python
_RE_VENCIMENTO = re.compile(
    r'(?:vencimento|venc\.)[:\s]+(\d{2}/\d{2}/\d{4})',
    re.IGNORECASE,
)
```

---

## Algoritmo de localização da guia no texto

```
1. Chamar extrair_texto_pdf(caminho) → obtém texto_completo, scanned, documentos_capa
2. Se scanned → retornar {"encontrado": False, "scanned": True}
3. Filtrar documentos_capa onde tipo.lower() em {"guia", "comprovante de pagamento de custas"}
4. Para cada doc_id filtrado:
   a. Encontrar todas as ocorrências de doc_id em texto_completo
   b. Para cada ocorrência, extrair janela de ±N caracteres (propor: 1500)
   c. Aplicar _extrair_valor_guia(janela)
   d. Se retornar dict válido (match em valor_total ou detalhamento) → usar este
5. Se nenhum doc_id produzir match → retornar {"encontrado": False, "scanned": False}
```

> **Nota:** O `doc_id` aparece na capa (tabela) e na página da guia. A ocorrência na capa não terá o contexto de valores; a ocorrência na guia terá. Testar janelas ao redor de cada ocorrência garante que encontraremos a correta.

---

## Dependências a instalar

**Nenhuma.** A solução reusa PyMuPDF (`pymupdf`) já presente no projeto.

---

## Critérios de aceite mensuráveis

- [ ] `extrair_custas_iniciais(PDF_REAL)` retorna `{"encontrado": True, "valor_total": "266,95", "valor_total_centavos": 26695}`
- [ ] O detalhamento do PDF real contém ao menos 4 dos 6 itens esperados (Distribuidor, Mandados, Ofícios, Contador, Custas, Diligências)
- [ ] `doc_id` retornado é `"206426308"` e `numero_guia` é `"001-9"`
- [ ] `extrair_texto_pdf(PDF_REAL)` inclui `"custas_iniciais"` no dict de retorno
- [ ] Teste mock com guia sem detalhamento retorna `encontrado: True` com `valor_total` preenchido e `detalhamento` como dict vazio
- [ ] Teste com PDF sem guia (mock) retorna `{"encontrado": False}`
- [ ] Teste com PDF scanned retorna `{"encontrado": False, "scanned": True}`
- [ ] Os 6 testes existentes em `test_extrator_pdf.py` continuam passando sem modificação
- [ ] CLI `testar_pdf.py` exibe valor das custas iniciais na saída formatada (tabela rich e ANSI)
- [ ] CLI inclui `"custas_iniciais"` no JSON de saída

---

## Decisões de baixa reversibilidade

**Nenhuma.** Esta feature é puramente aditiva:
- Novo campo `"custas_iniciais"` em dict de retorno (não quebra callers existentes)
- Novas funções auxiliares privadas (prefixo `_`)
- Sem alteração de schema de banco, protocolo de rede, ou dependência externa

---

## Riscos e pontos de atenção

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Formato de guia varia entre tribunais | Alta | Médio | Regex com múltiplos padrões + fallback permissivo. Documentar no código que regex são específicos ao TJDFT e podem precisar de ajuste para outros tribunais. |
| `doc_id` aparece em contexto não-guia | Média | Médio | Heurística de janela + validação de contexto (presença de "Valor total" ou "Número da Guia" na janela). |
| False positive em valor monetário (outros valores no PDF) | Média | Baixo | Priorizar match próximo a doc_id + contexto de guia. Não fazer busca global por "R$" no PDF. |
| Performance em PDFs muito grandes | Baixa | Baixo | `str.find()` em loop sobre texto_completo é O(n) por ocorrência. PDF de 722 páginas é aceitável. |
| Scanned PDF não detectado como scanned | Baixa | Médio | Reusar flag `scanned` já calculada por `extrair_texto_pdf()`, que é testada. |

---

## Notas para o executor

1. **Ordem de implementação:**
   1. Implementar `_parse_valor_monetario()` (função pura, fácil de testar isoladamente)
   2. Implementar `_extrair_valor_guia()` com regex e testes rápidos via `pytest -k test_novo -s`
   3. Implementar `extrair_custas_iniciais()` com a lógica de janela
   4. Integrar em `extrair_texto_pdf()`
   5. Atualizar CLI
   6. Rodar suite completa: `pytest agente/tests/test_extrator_pdf.py -v`

2. **Constante de janela:** Use `JANELA_GUIA = 1500` (caracteres antes/depois do doc_id). Se o regex não encontrar nada, pode expandir para `2000`. Documentar no código.

3. **Teste com PDF real:** O caminho já está definido em `test_extrator_pdf.py` como `PDF_REAL`. Basta adicionar novas funções de teste.

4. **Formato de valor:** Manter sempre string com vírgula decimal (formato brasileiro) no campo `valor_total`. O campo `valor_total_centavos` deve ser `int` sem sinal.

5. **Guia sem detalhamento:** Quando a guia não tiver lista de itens (ex: guia simplificada), `detalhamento` deve ser `{}` (dict vazio), nunca `None`.
