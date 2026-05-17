"""
Testes unitários para o extrator de PDFs judiciais.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from modulos.extrator_pdf import (
    extrair_texto_pdf,
    _isolar_dispositivo,
    extrair_documentos_capa,
    extrair_custas_iniciais,
    _parse_valor_monetario,
    _extrair_valor_guia,
)


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


@patch("modulos.extrator_pdf.os.path.exists", return_value=True)
@patch("modulos.extrator_pdf.fitz.open")
def test_nao_marcar_scanned_capa_imagem(mock_fitz_open, _mock_exists):
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


@patch("modulos.extrator_pdf.os.path.exists", return_value=True)
@patch("modulos.extrator_pdf.fitz.open")
def test_double_close_nao_ocorre(mock_fitz_open, _mock_exists):
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


# ========================================================================
# TESTES — Extração de custas iniciais
# ========================================================================


def test_extrair_texto_pdf_inclui_custas_iniciais():
    """extrair_texto_pdf deve incluir 'custas_iniciais' no dict de retorno."""
    resultado = extrair_texto_pdf(PDF_REAL)
    assert "custas_iniciais" in resultado
    custas = resultado["custas_iniciais"]
    assert custas["encontrado"] is True
    assert custas["valor_total"] == "266,95"
    assert custas["valor_total_centavos"] == 26695
    assert custas["doc_id"] == "206426308"


def test_extrair_custas_iniciais_pdf_real():
    """Extrai valor das custas iniciais do PDF real (guia na página 53)."""
    resultado = extrair_custas_iniciais(PDF_REAL)

    assert resultado["encontrado"] is True
    assert resultado["scanned"] is False
    assert resultado["valor_total"] == "266,95"
    assert resultado["valor_total_centavos"] == 26695
    assert resultado["doc_id"] == "206426308"
    assert resultado["numero_guia"] == "001-9"
    assert resultado["vencimento"] == "11/08/2024"

    detalhamento = resultado.get("detalhamento", {})
    # Deve conter ao menos 4 dos 6 itens esperados
    assert len(detalhamento) >= 4, f"Esperado >= 4 itens, obtido: {detalhamento}"

    # Valida itens específicos
    assert detalhamento.get("distribuidor") == "10,74"
    assert detalhamento.get("mandados") == "8,83"
    assert detalhamento.get("oficios") == "8,83"
    assert detalhamento.get("contador") == "13,21"
    assert detalhamento.get("custas") == "203,16"
    assert detalhamento.get("diligencias") == "22,18"


def test_extrair_valor_guia_sem_detalhamento():
    """Mock de guia com valor total mas sem detalhamento por item."""
    texto_mock = (
        "Número da Guia: 042-1\n"
        "Vencimento: 15/09/2024\n"
        "Valor Total: R$ 150,00\n"
    )
    resultado = _extrair_valor_guia(texto_mock)

    assert resultado is not None
    assert resultado["valor_total"] == "150,00"
    assert resultado["valor_total_centavos"] == 15000
    assert resultado["detalhamento"] == {}
    assert resultado["numero_guia"] == "042-1"
    assert resultado["vencimento"] == "15/09/2024"


def test_extrair_custas_iniciais_sem_guia():
    """PDF sem documento do tipo guia deve retornar encontrado=False."""
    documentos_sem_guia = [
        {"doc_id": "123456", "tipo": "Petição Inicial", "nome": "Petição", "data_assinatura": "01/01/2024"},
        {"doc_id": "123457", "tipo": "Mandado", "nome": "Mandado", "data_assinatura": "02/01/2024"},
    ]
    resultado = extrair_custas_iniciais(
        "/fake/path.pdf",
        texto_completo="Texto qualquer sem guia.",
        documentos_capa=documentos_sem_guia,
        scanned=False,
    )

    assert resultado["encontrado"] is False
    assert resultado["scanned"] is False


def test_extrair_custas_iniciais_scanned():
    """PDF scanned deve retornar encontrado=False e scanned=True."""
    resultado = extrair_custas_iniciais(
        "/fake/scanned.pdf",
        texto_completo="",
        documentos_capa=[{"doc_id": "999999", "tipo": "Guia", "nome": "Guia", "data_assinatura": "01/01/2024"}],
        scanned=True,
    )

    assert resultado["encontrado"] is False
    assert resultado["scanned"] is True


# ========================================================================
# TESTES — Utilitário _parse_valor_monetario
# ========================================================================


def test_parse_valor_monetario_varios_formatos():
    """Converte strings monetárias em (str_formatada, centavos)."""
    assert _parse_valor_monetario("R$ 1.234,56") == ("1234,56", 123456)
    assert _parse_valor_monetario("1234,56") == ("1234,56", 123456)
    assert _parse_valor_monetario("R$ 266,95") == ("266,95", 26695)
    assert _parse_valor_monetario("10,74") == ("10,74", 1074)
    assert _parse_valor_monetario("") == ("", 0)
    assert _parse_valor_monetario("abc") == ("", 0)
