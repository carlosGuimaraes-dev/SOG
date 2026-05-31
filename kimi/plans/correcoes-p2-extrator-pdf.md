# Plano técnico — Correções P2 no extrator de PDF

> **Escopo:** Duas ressalvas de prioridade P2 em `agente/src/modulos/extrator_pdf.py`
> **Data:** 2026-05-17

---

## Visão geral da solução

1. **Double-close PyMuPDF:** Remover `doc.close()` do bloco `except` da função `extrair_texto_pdf()`, mantendo-o exclusivamente no `finally`. O `finally` sempre executa, então o recurso é liberado exatamente uma vez.

2. **Falso positivo em detecção de scanned:** Substituir a heurística "qualquer página com pouco texto + imagem marca o documento inteiro" por uma heurística agregada: o documento só é considerado scanned se mais de 80% das páginas forem image-only **E** a média de texto por página for inferior a 100 caracteres. Isso elimina falsos positivos em PDFs cuja capa contenha brasão/imagem com poucas palavras, mas cujo corpo seja texto selecionável.

---

## Arquivos

| Ação | Caminho |
|------|---------|
| Modificar | `agente/src/modulos/extrator_pdf.py` |
| Modificar | `agente/tests/test_extrator_pdf.py` |

---

## Interfaces e contratos

- **Sem alteração de assinatura.** `extrair_texto_pdf(caminho: str) -> Dict[str, Any]` mantém a mesma interface.
- **Sem alteração de schema de retorno.** Os mesmos campos são retornados; apenas a lógica interna do campo `scanned` muda.
- **Sem impacto em callers.** `extrair_custas_iniciais()` consome `scanned` do dict — comportamento esperado é idêntico para PDFs realmente scanned e para PDFs de texto.

---

## Dependências

Nenhuma. Não são necessárias novas bibliotecas.

---

## Critérios de aceite mensuráveis

- [ ] `doc.close()` aparece **apenas** no bloco `finally` de `extrair_texto_pdf()`; removido do `except`.
- [ ] Teste mock simula exceção no loop de páginas (`page.get_text()` levanta) e verifica que `mock_doc.close.assert_called_once()` — nenhum double-close.
- [ ] Teste mock com 5 páginas (1 image-only + 4 com texto extenso) retorna `scanned=False` — falso positivo eliminado.
- [ ] Teste mock com 2 páginas 100% image-only (`test_detectar_scanned_pdf` existente) continua retornando `scanned=True`.
- [ ] Teste com PDF real (`test_extrair_texto_pdf_real`) continua passando e retornando `scanned=False`.
- [ ] Todos os testes em `agente/tests/test_extrator_pdf.py` passam (`pytest agente/tests/test_extrator_pdf.py -v`).

---

## Detalhes de implementação

### 1. Double-close (linhas ~626-632)

**Código atual:**
```python
    except Exception as exc:
        resultado_base["erro"] = f"Erro ao processar páginas: {exc}"
        erro(f"Falha ao processar páginas do PDF: {exc}")
        doc.close()          # ← REMOVER
        return resultado_base
    finally:
        doc.close()
```

**Código corrigido:**
```python
    except Exception as exc:
        resultado_base["erro"] = f"Erro ao processar páginas: {exc}"
        erro(f"Falha ao processar páginas do PDF: {exc}")
        return resultado_base
    finally:
        doc.close()
```

### 2. Scanned detection — heurística agregada (linhas ~598-625)

**Código atual:**
```python
    texto_por_pagina: List[str] = []
    partes_texto: List[str] = []
    scanned = False

    try:
        for page in doc:
            altura = page.rect.height
            texto_bruto = page.get_text()
            # ... extração de blocos ...
            pagina_limpa = "\n".join(blocos_limpos)
            texto_por_pagina.append(pagina_limpa)
            partes_texto.append(pagina_limpa)

            # Scanned detection: pouco texto selecionável + presença de imagens
            if len(texto_bruto.strip()) < 30 and page.get_images():
                scanned = True
```

**Código corrigido:**
```python
    texto_por_pagina: List[str] = []
    partes_texto: List[str] = []
    paginas_scanned = 0
    total_texto_bruto = 0

    try:
        for page in doc:
            altura = page.rect.height
            texto_bruto = page.get_text()
            total_texto_bruto += len(texto_bruto.strip())

            # Contabiliza candidatas a scanned (avaliação global após o loop)
            if len(texto_bruto.strip()) < 30 and page.get_images():
                paginas_scanned += 1

            # ... extração de blocos (sem alteração) ...
            blocks = page.get_text("blocks")
            blocos_limpos: List[str] = []
            for block in blocks:
                if len(block) < 5:
                    continue
                _x0, y0, _x1, y1, texto_block = block[:5]
                if y1 < _MARGEM_VERTICAL or y0 > altura - _MARGEM_VERTICAL:
                    continue
                blocos_limpos.append(texto_block)

            pagina_limpa = "\n".join(blocos_limpos)
            texto_por_pagina.append(pagina_limpa)
            partes_texto.append(pagina_limpa)

        # Scanned detection global: heurística agregada
        num_paginas = len(doc)
        if num_paginas > 0:
            proporcao_scanned = paginas_scanned / num_paginas
            media_texto = total_texto_bruto / num_paginas
            scanned = proporcao_scanned > 0.8 and media_texto < 100
        else:
            scanned = False
```

**Observação:** A variável `scanned` precisa ser inicializada antes do `try` (ou receber default `False`) para estar disponível no dict de retorno caso o loop execute sem exceção.

```python
    scanned = False  # inicializa antes do try
```

### 3. Testes novos / atualizados

#### 3.1 Teste de double-close

```python
@patch("modulos.extrator_pdf.os.path.exists", return_value=True)
@patch("modulos.extrator_pdf.fitz.open")
def test_nao_faz_double_close_em_excecao(mock_fitz_open, _mock_exists):
    """Se exceção ocorre no loop de páginas, close() deve ser chamado apenas 1 vez."""
    mock_doc = MagicMock()
    mock_doc.__len__ = MagicMock(return_value=1)

    mock_page = MagicMock()
    mock_page.rect.height = 800
    mock_page.get_text.side_effect = RuntimeError("simulated error")

    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
    mock_doc.close = MagicMock()

    mock_fitz_open.return_value = mock_doc

    resultado = extrair_texto_pdf("/fake/error.pdf")

    assert "Erro ao processar páginas" in resultado["erro"]
    mock_doc.close.assert_called_once()
```

#### 3.2 Teste de falso positivo eliminado

```python
@patch("modulos.extrator_pdf.os.path.exists", return_value=True)
@patch("modulos.extrator_pdf.fitz.open")
def test_capa_image_only_nao_marca_scanned(mock_fitz_open, _mock_exists):
    """PDF com capa image-only e páginas de texto não deve ser marcado como scanned."""

    def _make_page(texto: str, tem_imagem: bool):
        p = MagicMock()
        p.rect.height = 800
        p.get_images.return_value = [("ref", 0, 0, 0, 0, 0, 0)] if tem_imagem else []

        def _fake_get_text(mode=None):
            if mode == "blocks":
                return [(0, 100, 500, 200, texto, 0, 0)]
            return texto

        p.get_text.side_effect = _fake_get_text
        return p

    mock_doc = MagicMock()
    mock_doc.__len__ = MagicMock(return_value=5)

    paginas = [
        _make_page("Brasão", True),  # candidata a scanned
        _make_page("Texto extenso da página 1 com muitas palavras sobre o processo judicial.", False),
        _make_page("Texto extenso da página 2 com mais informações do processo.", False),
        _make_page("Texto extenso da página 3 com fundamentação jurídica.", False),
        _make_page("Texto extenso da página 4 com dispositivo da sentença.", False),
    ]

    mock_doc.__iter__ = MagicMock(return_value=iter(paginas))
    mock_doc.close = MagicMock()

    mock_fitz_open.return_value = mock_doc

    resultado = extrair_texto_pdf("/fake/mixed.pdf")

    assert resultado["scanned"] is False
    assert resultado["num_paginas"] == 5
```

#### 3.3 Teste existente `test_detectar_scanned_pdf`

Este teste **não precisa ser alterado** — com a nova heurística:
- 2 páginas, ambas com texto `"a"` (<30 chars) + imagens
- `paginas_scanned = 2`, `total_texto_bruto = 2`
- `proporcao_scanned = 2/2 = 1.0 > 0.8` ✅
- `media_texto = 2/2 = 1 < 100` ✅
- Resultado: `scanned=True` (mantido)

---

## Decisões de baixa reversibilidade

**Nenhuma.** Ambas as correções são puramente internas à função `extrair_texto_pdf()`:
- O double-close é um bug; a correção não altera comportamento observável além de eliminar erro.
- A heurística de scanned é ajustável sem impactar contratos externos — os thresholds (`0.8`, `100`) são constantes internas e podem ser refinados futuramente.

---

## Riscos e pontos de atenção

| Risco | Mitigação |
|-------|-----------|
| Heurística nova pode deixar de detectar como "scanned" um PDF que antes era detectado corretamente | Teste existente `test_detectar_scanned_pdf` cobre 100% image-only e continua passando. O PDF real também continua como não-scanned. |
| Variável `scanned` não inicializada antes do `try` pode causar `UnboundLocalError` se o loop nunca iniciar (doc vazio) | Inicializar `scanned = False` antes do bloco `try`. |
| Divisão por zero se `len(doc) == 0` | Guarda `if num_paginas > 0:` antes do cálculo da proporção. |
| Mock de `test_detectar_scanned_pdf` retorna `get_text()` com `"a"` para texto bruto; `total_texto_bruto` soma `len("a")=1` por página. Isso funciona, mas a soma é de *comprimento* do texto, não de caracteres stripped | O comportamento é equivalente para o mock. O teste continua válido. |

---

## Checklist do executor

- [ ] `doc.close()` removido do `except`, preservado no `finally`
- [ ] `scanned = False` inicializado antes do `try`
- [ ] `paginas_scanned` e `total_texto_bruto` acumulados dentro do loop
- [ ] Heurística global aplicada após o loop com guarda `num_paginas > 0`
- [ ] Teste `test_nao_faz_double_close_em_excecao` criado e passando
- [ ] Teste `test_capa_image_only_nao_marca_scanned` criado e passando
- [ ] Teste `test_detectar_scanned_pdf` verificado e passando
- [ ] Teste `test_extrair_texto_pdf_real` verificado e passando
- [ ] Suite completa `pytest agente/tests/test_extrator_pdf.py -v` verde
