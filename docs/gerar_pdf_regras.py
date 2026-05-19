#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um PDF formatado para mapeamento de custas do SISTJWEB/TJDFT.

O PDF contém tabelas vazias para preenchimento manual por área do direito,
mais um exemplo preenchido (Cível Comum) como referência.
"""

from pathlib import Path
from fpdf import FPDF

# Larguras das colunas da tabela (soma = 170 mm, largura útil A4 com margens 20 mm)
COL_WIDTHS = [45, 45, 25, 55]
HEADERS = ["Item da Guia", "Item de Cálculo", "Quantidade", "Observações"]
CELL_HEIGHT = 8  # mm


def _draw_table_header(pdf: FPDF) -> None:
    """Desenha o cabeçalho da tabela."""
    pdf.set_font("Arial", "B", 10)
    for w, h in zip(COL_WIDTHS, HEADERS):
        pdf.cell(w, CELL_HEIGHT, h, border=1, align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln()


def _draw_empty_row(pdf: FPDF) -> None:
    """Desenha uma linha vazia da tabela."""
    pdf.set_font("Arial", "", 10)
    for w in COL_WIDTHS:
        pdf.cell(w, CELL_HEIGHT, "", border=1, align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln()


def draw_empty_table(pdf: FPDF, rows: int) -> None:
    """Desenha uma tabela vazia com N linhas."""
    _draw_table_header(pdf)
    for _ in range(rows):
        _draw_empty_row(pdf)


def draw_filled_table(pdf: FPDF, data: list[list[str]]) -> None:
    """Desenha uma tabela preenchida com os dados fornecidos."""
    _draw_table_header(pdf)
    pdf.set_font("Arial", "", 10)
    for row in data:
        for w, val in zip(COL_WIDTHS, row):
            pdf.cell(w, CELL_HEIGHT, val, border=1, align="C", new_x="RIGHT", new_y="TOP")
        pdf.ln()


def add_area_page(pdf: FPDF, area_name: str) -> None:
    """Adiciona uma página para uma área do direito com tabela vazia."""
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Área: {area_name}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(2)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(
        0,
        6,
        (
            "Preencher com os itens que aparecem no dropdown 'Item da Guia' "
            "e o radio 'Item de Cálculo' correspondente para processos típicos desta área."
        ),
    )
    pdf.ln(3)

    draw_empty_table(pdf, rows=8)
    pdf.ln(3)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, CELL_HEIGHT, "Existe isenção de custas nesta área? [ ] Sim  [ ] Não", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, CELL_HEIGHT, "Se sim, em quais casos? _________________________________", new_x="LMARGIN", new_y="NEXT")


def main() -> None:
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    # ------------------------------------------------------------------
    # Página 1 — Título e Instruções
    # ------------------------------------------------------------------
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Mapeamento de Custas - SISTJWEB / TJDFT", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 11)
    instructions = [
        (
            "Este documento serve para anotar quais itens da guia de custas são "
            "usados em cada área do direito no SISTJWEB do TJDFT."
        ),
        (
            "Para preencher, abra o SISTJWEB e acesse a planilha de custas de um "
            "processo típico da área. Anote os itens que aparecem no dropdown "
            "'Item da Guia' e o radio 'Item de Cálculo' correspondente."
        ),
        "Depois de preencher todas as áreas, envie este documento de volta.",
    ]
    for text in instructions:
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)

    # ------------------------------------------------------------------
    # Páginas 2–4 — Áreas (cada uma em nova página)
    # ------------------------------------------------------------------
    for area in ("Criminal", "Família", "Fazenda Pública"):
        add_area_page(pdf, area)

    # ------------------------------------------------------------------
    # Página 5 — Exemplo preenchido (Cível Comum)
    # ------------------------------------------------------------------
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Exemplo: Área Cível Comum (já mapeada)", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(2)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "Use este exemplo como referência do nível de detalhe esperado.")
    pdf.ln(3)

    example_data = [
        ["Distribuidor", "D-I-a", "1", ""],
        ["Distribuidor", "D-II-a", "1", ""],
        ["Contador", "E-I", "1", ""],
        ["Ofícios", "G-XX-a parte 2", "1", "Usar IDs dos ofícios do PJe"],
        ["Custas", "G-I", "1", "Usar valor da causa atualizado"],
    ]
    draw_filled_table(pdf, example_data)

    # ------------------------------------------------------------------
    # Como devolver
    # ------------------------------------------------------------------
    pdf.ln(8)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, CELL_HEIGHT, "Como devolver", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, CELL_HEIGHT, "1. Preencha as tabelas acima.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, CELL_HEIGHT, "2. Envie de volta para quem solicitou.", new_x="LMARGIN", new_y="NEXT")

    # ------------------------------------------------------------------
    # Saída
    # ------------------------------------------------------------------
    output_path = Path(__file__).resolve().parent / "regras_custas_tjdft.pdf"
    pdf.output(str(output_path))
    print(f"PDF gerado com sucesso: {output_path}")


if __name__ == "__main__":
    main()
