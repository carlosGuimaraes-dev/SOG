# Plano: Script utilitário `tools/testar_pdf.py`

## Visão geral
Script standalone que extrai texto de um PDF judicial local, isola o DISPOSITIVO via heurística e repassa ao `extrair_sentenca()` existente. Saída em JSON no terminal.

## Decisões técnicas

1. **Biblioteca de PDF**: `pymupdf` (fitz) — extrai por blocos de layout, melhor para localizar o dispositivo em PDFs do PJE/TJDFT. ⚠️ **Licença AGPL-3.0**; como é tool interna (não distribuída), aceitável. Se projeto for redistribuído, trocar por `pdfplumber` (MIT) — interface do script isola a lib, portanto **reversível**.
2. **Heurística DISPOSITIVO**: regex case-insensitive busca `ANTE O EXPOSTO`, `DISPOSITIVO` ou `DECIDO`; pega tudo a partir da última ocorrência até o final do documento. Se ausente, passa texto completo.
3. **Localização**: `tools/testar_pdf.py` na raiz. Importa `extrair_sentenca` via `sys.path.insert` apontando para `agente/src`. Scripts utilitários não pertencem ao runtime do agente.
4. **PDF scanned**: se `page.get_text()` retornar <10 chars em todas as páginas e houver imagens, aborta com mensagem clara sugerindo OCR externo.

## Arquivos

- **Criar**: `tools/testar_pdf.py`
- **Modificar**: `agente/requirements.txt` — adicionar `pymupdf==1.24.5`

## Interface do script

```bash
python tools/testar_pdf.py <caminho_do_pdf> [--area civel|trabalhista] [--debug]
```

Saída: JSON com campos do `extrair_sentenca` + `_dispositivo_extraido` (bool) + `_paginas`.

## Dependências

- `pymupdf==1.24.5` (verificar versão estável no PyPI no momento da instalação)

## Critérios de aceite

- [ ] Extrai texto de PDF com texto selecionável e retorna JSON válido.
- [ ] Isola corretamente o dispositivo quando há bloco "ANTE O EXPOSTO".
- [ ] Detecta PDF scanned e exibe aviso human-readable em `stderr` com exit code `2`.
- [ ] Funciona com import relativo de `agente/src/modulos/extrator_sentenca.py`.
- [ ] `--debug` imprime o texto bruto do dispositivo antes do JSON.

## Riscos

- **AGPL-3.0**: se projeto for redistribuído, trocar por `pdfplumber`.
- **Layout variável do PJE**: heurística pode falhar em decisões interlocutórias ou documentos atípicos; fallback de passar texto completo mitiga.
o da secao DISPOSITIVO:**
   - Buscar regex: `(DISPOSITIVO|DECIDO|ACORDAM|ACORDO)[\s\n]*[:\n-]*`
   - Se encontrado, marcar inicio = fim do match.
   - Se nao encontrado, usar inicio do texto (fallback).

3. **Delimitacao do fim do DISPOSITIVO:**
   - Buscar regex: `(Intimem-se|Publique-se|P\.I\.|Registrar|Cumpra-se|De-se ciencia|Apos|Ciencia d[eoa]|Traslado)`
   - Fim do DISPOSITIVO = inicio do match (ou fim do documento se nao houver match).

4. **Fallback:** Se a heuristica acima retornar menos de 200 caracteres, retornar o texto completo do documento (sem remocao de cabecalho/rodape) para que o extrator_sentenca tente trabalhar com o maximo de contexto.

### 2.3 PDFs Scanned (Image-only)

`pdfplumber` retornara texto vazio ou menos de 50 caracteres totais. Detectar isso e levantar excecao `PDFSemTextoSelecionavel` com mensagem informativa. **OCR fora do escopo desta entrega** — documentar como limitacao conhecida no README e no help do CLI.

### 2.4 Formatacao do CLI — `rich`

Adicionar `rich` ao `requirements.txt`. Usar `rich.console.Console`, `rich.json.JSON`, `rich.panel.Panel` para saida colorida e estruturada. Alternativa sem `rich` (colorama+json) deixaria o CLI feio; `rich` e MIT, leve (~150KB), amplamente adotado.

---

## 3. Arquivos a Criar / Modificar / Deletar

### Criar

| Caminho | Descricao |
|---------|-----------|
| `agente/src/modulos/extrator_pdf.py` | Modulo de extracao de texto de PDF |
| `agente/tests/test_extrator_pdf.py` | Testes unitarios |
| `tools/testar_pdf.py` | Script CLI utilitario |
| `.kimi/plans/extrator-pdf.md` | Este plano |

### Modificar

| Caminho | Descricao |
|---------|-----------|
| `agente/requirements.txt` | Adicionar `pdfplumber==0.11.5` e `rich==13.9.4` |

### NAO modificar (garantia de nao-regressao)

- `agente/src/modulos/extrator_sentenca.py`
- `agente/src/modulos/parser.py`
- `agente/src/modulos/pje.py`
- Qualquer outro modulo do pipeline existente

---

## 4. Interfaces e Contratos

### 4.1 `agente/src/modulos/extrator_pdf.py`

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class MetadadosPDF:
    caminho: str
    num_paginas: int
    tamanho_bytes: int
    tem_texto: bool          # False se image-only
    texto_completo: str      # Todo o texto extraido (pos-remocao cabecalho/rodape)
    dispositivo: str         # Secao isolada do DISPOSITIVO (ou texto_completo em fallback)


class PDFSemTextoSelecionavel(Exception):
    """Levantado quando o PDF nao contem texto selecionavel (scanned/image-only)."""
    pass


class PDFCorrompidoError(Exception):
    """Levantado quando o arquivo nao e um PDF valido ou esta corrompido."""
    pass


def extrair_texto_pdf(caminho: str, area_cabecalho_pct: float = 0.08, area_rodape_pct: float = 0.08) -> MetadadosPDF:
    """
    Abre o PDF em `caminho`, extrai texto pagina a pagina removendo cabecalho/rodape
    por posicao vertical, e isola a secao DISPOSITIVO via heuristica de palavras-chave.

    Args:
        caminho: caminho absoluto ou relativo do arquivo PDF.
        area_cabecalho_pct: fracao da altura da pagina a descartar no topo (0.0–1.0).
        area_rodape_pct: fracao da altura da pagina a descartar na base (0.0–1.0).

    Returns:
        MetadadosPDF com texto completo, dispositivo isolado e flags de diagnostico.

    Raises:
        PDFSemTextoSelecionavel: se o PDF nao tiver texto selecionavel (image-only).
        PDFCorrompidoError: se o arquivo nao for um PDF valido.
        FileNotFoundError: se o arquivo nao existir.
    """
    ...


def _remover_cabecalho_rodape(pagina, area_cabecalho_pct: float, area_rodape_pct: float) -> str:
    """Extrai texto de uma pagina do pdfplumber descartando regioes de cabecalho/rodape."""
    ...


def _isolar_dispositivo(texto: str) -> str:
    """
    Heuristica para isolar a secao DISPOSITIVO de uma sentenca judicial.
    Retorna o texto do dispositivo ou o texto original em fallback.
    """
    ...
```

### 4.2 `tools/testar_pdf.py` — CLI

```
usage: testar_pdf.py [-h] [-v] [--llm] pdf

Extrai texto de um PDF judicial e passa pelo pipeline de analise do SOG.

positional arguments:
  pdf           Caminho do arquivo PDF

options:
  -h, --help    show this help message and exit
  -v, --verbose Mostra o texto bruto extraido do PDF
  --llm         Forca uso do LLM no extrator de sentenca
```

**Fluxo de execucao:**
1. `extrair_texto_pdf(caminho_pdf)` -> `MetadadosPDF`
2. `extrair_sentenca(metadados.dispositivo, area="civel", forcar_llm=args.llm)` -> dict
3. `parse_comprovante_pagamento(metadados.texto_completo)` -> dict (busca comprovantes em todo o texto)
4. Monta resultado unificado: `{ "pdf": metadados, "sentenca": ..., "comprovantes": [...] }`
5. Imprime com `rich` (JSON + resumo executivo em painel).

---

## 5. Dependencias a Instalar

```text
# Adicionar ao agente/requirements.txt
pdfplumber==0.11.5
rich==13.9.4
```

**Verificacao de licenca:**
- `pdfplumber`: MIT ✅
- `rich`: MIT ✅
- Ambas mantidas ativamente (ultimo commit < 3 meses).

---

## 6. Criterios de Aceite Mensuraveis

### 6.1 Funcionais

- [ ] `python tools/testar_pdf.py docs/processos/0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf` executa sem erro e exibe:
  - Metadados do PDF (paginas, tamanho, tem_texto=True)
  - Texto do DISPOSITIVO extraido (contendo "MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA")
  - Resultado da regex: sucumbente_nome, valor_condenacao, honorarios_percentual, suspensao_exigibilidade
  - Resumo executivo em painel colorido
- [ ] Flag `--verbose` exibe o texto bruto completo extraido do PDF antes do resultado.
- [ ] Flag `--llm` forca chamada ao LLM (testar com `OPENAI_API_KEY` setada ou mockar no teste).
- [ ] PDF corrompido (criar fixture `tests/fixtures/corrompido.pdf` ou usar arquivo invalido) gera `PDFCorrompidoError` com mensagem clara.
- [ ] PDF sem texto (criar fixture com PDF de 1 pagina image-only) gera `PDFSemTextoSelecionavel` com mensagem informativa.

### 6.2 Testes

- [ ] `pytest agente/tests/test_extrator_pdf.py -v` passa com 100% de sucesso.
- [ ] Testes cobrem:
  - Extracao do PDF real do projeto (>= 1 pagina, tem texto)
  - Heuristica de DISPOSITIVO encontra "MARIA APARECIDA..." no PDF real
  - Remocao de cabecalho/rodape (verificar que brasao/paginacao nao aparece no texto extraido)
  - PDF corrompido levanta `PDFCorrompidoError`
  - PDF image-only levanta `PDFSemTextoSelecionavel`
  - Metadados corretos (num_paginas > 0, tamanho_bytes > 0)

### 6.3 Nao-regressao

- [ ] `pytest agente/tests/test_extrator_sentenca.py -v` continua passando (sem modificacao no extrator).
- [ ] `pytest agente/tests/test_parser.py -v` continua passando (sem modificacao no parser).
- [ ] Pipeline existente (pje.py) nao e afetado (nenhum import circular, nenhuma mudanca de assinatura).

---

## 7. Riscos e Pontos de Atencao

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| PDF real tem layout atipico e cabecalho/rodape nao sao 8% | Media | Medio | Parametro `area_cabecalho_pct`/`area_rodape_pct` ajustavel; testar com PDF real antes de finalizar |
| DISPOSITIVO nao encontrado por variacao de terminologia | Baixa | Medio | Fallback para texto completo; adicionar mais palavras-chave ao regex se necessario |
| pdfplumber nao disponivel em certas plataformas (depende de pdfminer.six que usa ctypes) | Baixa | Baixo | pdfplumber e pure Python com bindings C leves; testar no ambiente Docker do projeto |
| Dependencia `rich` conflita com outra lib do projeto | Baixa | Baixo | rich e autocontido; verificar antes com `pip install -r requirements.txt` |
| PDF real e scanned (image-only) e nao sabemos | Baixa | Alto | Verificar com `pdfplumber` antes de codificar; se for scanned, criar teste com PDF sintetico image-only |

---

## 8. Checklist de Implementacao (para o executor)

1. [ ] Adicionar `pdfplumber==0.11.5` e `rich==13.9.4` ao `agente/requirements.txt`
2. [ ] Criar `agente/src/modulos/extrator_pdf.py` com:
   - [ ] Classes de excecao (`PDFSemTextoSelecionavel`, `PDFCorrompidoError`)
   - [ ] `MetadadosPDF` dataclass
   - [ ] `extrair_texto_pdf()`
   - [ ] `_remover_cabecalho_rodape()`
   - [ ] `_isolar_dispositivo()`
3. [ ] Criar `agente/tests/test_extrator_pdf.py` com testes listados nos criterios de aceite
4. [ ] Criar `tools/testar_pdf.py` com argparse + rich
5. [ ] Executar script com PDF real e validar saida
6. [ ] Rodar suite completa de testes do agente: `pytest agente/tests/ -v`
7. [ ] Salvar este plano em `.kimi/plans/extrator-pdf.md`
8. [ ] Atualizar `MEMORY.md` com decisao sobre biblioteca PDF

---

## 9. Apendice — Exemplo de Saida do CLI

```
$ python tools/testar_pdf.py docs/processos/0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf

+----------------------------------------+
|  SOG — Analise de PDF Judicial         |
+----------------------------------------+

📄 Metadados do PDF
   Paginas: 3
   Tamanho: 142 KB
   Tem texto selecionavel: Sim

📋 DISPOSITIVO extraido (487 caracteres)
   -----------------------------------
   ANTE O EXPOSTO, com fundamento no art. 487, inciso I, do CPC...
   condeno MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA ao
   cumprimento... montante de R$ 10.158,00...
   -----------------------------------

⚖️  Resultado da Analise
   +-------------------------+-----------------------------+
   | Sucumbente              | MARIA APARECIDA HERUNDINA.. |
   | Tipo                    | reu                         |
   | Valor da condenacao     | R$ 10.158,00                |
   | Honorarios              | 10%                         |
   | Suspensao exigibilidade | Sim (art. 98, § 3º)         |
   | Metodo                  | regex                       |
   | Score                   | 1.00                        |
   +-------------------------+-----------------------------+
```

---

*Plano criado em 2026-05-16 por CTO (SOUL).*
