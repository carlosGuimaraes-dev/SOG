"""
Testes unitários para o extrator de PDFs judiciais.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from modulos.extrator_pdf import extrair_texto_pdf, _isolar_dispositivo, extrair_documentos_capa


PDF_REAL = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "docs",
    "processos",
    "0732384-63.2024.8.07.0001-1778736791355-34616-processo.pdf",
)


# ========================================================================
# TESTES — Extração de PDF real
# ========================================================================


def test_extrair_texto_pdf_real():
    """Extrai texto de um PDF judicial real e valida os campos retornados."""
    resultado = extrair_texto_pdf(PDF_REAL)

    assert resultado["erro"] == "", f"Erro inesperado: {resultado['erro']}"
    assert resultado["num_paginas"] > 0
    assert len(resultado["texto_completo"]) > 100

    dispositivo = resultado["dispositivo"]
    dispositivo_lower = dispositivo.lower()
    assert (
        "condeno" in dispositivo_lower
        or "ante o exposto" in dispositivo_lower
    ), f"Dispositivo não contém 'condeno' nem 'ANTE O EXPOSTO': {dispositivo[:200]}"

    # Campo documentos_capa deve estar presente e populado
    assert "documentos_capa" in resultado
    assert len(resultado["documentos_capa"]) > 0


# ========================================================================
# TESTES — Erros
# ========================================================================


def test_pdf_nao_encontrado():
    """Caminho inexistente deve retornar erro preenchido."""
    resultado = extrair_texto_pdf("/caminho/inexistente/12345.pdf")
    assert resultado["erro"] != ""
    assert (
        "não encontrado" in resultado["erro"].lower()
        or "erro" in resultado["erro"].lower()
    )


# ========================================================================
# TESTES — Detecção de scanned
# ========================================================================


@patch("modulos.extrator_pdf.os.path.exists", return_value=True)
@patch("modulos.extrator_pdf.fitz.open")
def test_detectar_scanned_pdf(mock_fitz_open, _mock_exists):
    """Simula PDF scanned: pouco texto selecionável e presença de imagens."""
    mock_doc = MagicMock()
    mock_doc.__len__ = MagicMock(return_value=2)

    mock_page = MagicMock()
    mock_page.rect.height = 800
    mock_page.get_images.return_value = [("ref", 0, 0, 0, 0, 0, 0)]

    # get_text sem argumento → texto bruto curto
    # get_text("blocks") → blocos vazios (simula ausência de texto)
    def _fake_get_text(mode=None):
        if mode == "blocks":
            return []
        return "a"  # menos de 30 caracteres

    mock_page.get_text.side_effect = _fake_get_text

    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page, mock_page]))
    mock_doc.close = MagicMock()

    mock_fitz_open.return_value = mock_doc

    resultado = extrair_texto_pdf("/fake/scanned.pdf")

    assert resultado["scanned"] is True
    assert resultado["num_paginas"] == 2


# ========================================================================
# TESTES — Heurística de isolamento do dispositivo
# ========================================================================


def test_extrair_documentos_capa():
    """Extrai documentos da capa do PDF real e valida estrutura."""
    documentos = extrair_documentos_capa(PDF_REAL)

    assert len(documentos) > 0, "Esperado pelo menos 1 documento na capa"

    # Verifica estrutura mínima dos documentos extraídos
    for doc in documentos:
        assert "doc_id" in doc
        assert "data_assinatura" in doc
        assert "nome" in doc
        assert "tipo" in doc
        assert doc["doc_id"].isdigit()

    # Deve haver pelo menos um documento com tipo identificado
    com_tipo = [d for d in documentos if d["tipo"]]
    assert len(com_tipo) > 0, "Esperado pelo menos 1 documento com tipo identificado"

    # Tipos relevantes que sabemos existir no PDF real
    tipos_presentes = {d["tipo"] for d in documentos}
    assert "Mandado" in tipos_presentes or "Petição Inicial" in tipos_presentes


def test_isolar_dispositivo_com_palavra_dispositivo():
    """Deve isolar o trecho após 'DISPOSITIVO' até o terminador."""
    texto = (
        "Fundamento.\n\n"
        "DISPOSITIVO\n"
        "Ante o exposto, julgo procedente.\n"
        "Intimem-se.\n"
        "Assinado digitalmente."
    )
    dispositivo = _isolar_dispositivo(texto)
    assert "Ante o exposto" in dispositivo
    assert "Intimem-se" not in dispositivo
    assert "Assinado digitalmente" not in dispositivo


def test_isolar_dispositivo_ante_o_exposto_fallback():
    """Quando não há 'DISPOSITIVO', deve capturar 'ANTE O EXPOSTO'."""
    texto = (
        "Fundamento.\n\n"
        "ANTE O EXPOSTO, julgo procedente o pedido.\n"
        "Condene-se o réu.\n"
        "Intimem-se.\n"
        "Brasília, 01/01/2024."
    )
    dispositivo = _isolar_dispositivo(texto)
    assert "ANTE O EXPOSTO" in dispositivo
    assert "julgo procedente" in dispositivo
    assert "Intimem-se" not in dispositivo


def test_isolar_dispositivo_fallback_ultimos_25():
    """Quando nenhum padrão conhecido é encontrado, retorna últimos 25%."""
    texto = "A" * 1000 + "\nDISPOSITIVO NÃO PADRONIZADO\nB" * 10
    dispositivo = _isolar_dispositivo(texto)
    # Deve retornar algo (últimos 25%)
    assert len(dispositivo) > 0
    assert "NÃO PADRONIZADO" in dispositivo
