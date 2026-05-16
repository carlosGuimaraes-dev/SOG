---
name: pdf-processor
description: Processamento de PDFs para custas processuais. Extração de texto com pdfplumber, geração de guias com reportlab/weasyprint, preenchimento de formulários, validação de integridade, manipulação de múltiplas páginas e OCR com Tesseract.
---

# PDF Processor

## Resumo

Extração, geração e manipulação de PDFs no contexto de custas processuais, com foco em dados estruturados e evidências.

## Quando usar

- Extrair valor de custas de guias judiciais em PDF
- Gerar guias de pagamento preenchidas automaticamente
- Validar integridade de documentos recebidos
- Combinar múltiplos PDFs em um único arquivo
- Processar PDFs digitalizados (imagem)

## Padrões principais

### 1. Extração de texto com pdfplumber

```python
import pdfplumber

def extrair_texto_pdf(caminho: str) -> str:
    with pdfplumber.open(caminho) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def extrair_tabela(caminho: str):
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                yield table
```

### 2. Extração de dados estruturados

```python
import re

def extrair_valor_custas(texto: str) -> float:
    padrao = r"Valor total das custas.*?R\$\s*([\d.,]+)"
    match = re.search(padrao, texto, re.IGNORECASE)
    if match:
        valor_str = match.group(1).replace(".", "").replace(",", ".")
        return float(valor_str)
    raise ValueError("Valor de custas não encontrado")
```

### 3. Geração de guias com reportlab

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def gerar_guia(destino: str, numero: str, valor: float):
    c = canvas.Canvas(destino, pagesize=A4)
    c.drawString(100, 750, f"Processo: {numero}")
    c.drawString(100, 730, f"Valor: R$ {valor:.2f}")
    c.save()
```

### 4. Geração de guias com WeasyPrint (HTML → PDF)

```python
from weasyprint import HTML, CSS

def gerar_guia_html(destino: str, contexto: dict):
    html = f"""
    <html><body>
        <h1>Guia de Custas</h1>
        <p>Processo: {contexto['numero']}</p>
        <p>Valor: R$ {contexto['valor']:.2f}</p>
    </body></html>
    """
    HTML(string=html).write_pdf(destino)
```

### 5. Preenchimento de formulários PDF

```python
from pypdf import PdfReader, PdfWriter

def preencher_formulario(template: str, destino: str, campos: dict):
    reader = PdfReader(template)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.update_page_form_field_values(writer.pages[0], campos)
    with open(destino, "wb") as f:
        writer.write(f)
```

### 6. Validação de integridade

```python
import hashlib

def hash_pdf(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def validar_pdf(caminho: str) -> bool:
    try:
        with pdfplumber.open(caminho) as pdf:
            return len(pdf.pages) > 0
    except Exception:
        return False
```

### 7. Manipulação de múltiplas páginas

```python
from pypdf import PdfMerger, PdfReader

def mesclar_pdfs(saidas: list[str], destino: str):
    merger = PdfMerger()
    for pdf in saidas:
        merger.append(pdf)
    merger.write(destino)
    merger.close()

def dividir_pdf(caminho: str, paginas_por_arquivo: int = 1):
    reader = PdfReader(caminho)
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        with open(f"page_{i+1}.pdf", "wb") as f:
            writer.write(f)
```

### 8. OCR quando necessário (Tesseract)

```python
# Requer: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

def ocr_pdf(caminho: str) -> str:
    imagens = convert_from_path(caminho)
    texto = ""
    for img in imagens:
        texto += pytesseract.image_to_string(img, lang="por")
    return texto
```

## Anti-patterns

- Extrair texto com regex sobre bytes em vez de pdfplumber
- Não validar se o PDF está corrompido antes de processar
- Hardcodear posições de texto em PDFs gerados
- Ignorar que PDFs digitalizados precisam de OCR
- Não guardar hash de documentos recebidos para auditoria
- Usar reportlab para layouts complexos (prefira WeasyPrint)
