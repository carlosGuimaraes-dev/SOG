#!/usr/bin/env python3
"""Script CLI para testar extração de dados de PDFs judiciais."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Garante imports do agente/src quando rodado diretamente
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from modulos.extrator_pdf import extrair_texto_pdf
from modulos.extrator_sentenca import extrair_sentenca
from modulos.parser import processar_documentos

# rich é opcional — fallback para ANSI colors
_RICH_DISPONIVEL = False
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.json import JSON
    from rich.table import Table

    _RICH_DISPONIVEL = True
except ImportError:
    pass

# Cores ANSI para fallback
_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_RED = "\033[31m"
_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_CYAN = "\033[36m"
_ANSI_DIM = "\033[2m"


def _print_colorido(texto: str, cor: str = "") -> None:
    """Print com cor ANSI (safe para terminais sem suporte)."""
    if cor:
        print(f"{cor}{texto}{_ANSI_RESET}")
    else:
        print(texto)


def _montar_saida_colorida_rich(
    resultado_pdf: Dict[str, Any],
    resultado_sentenca: Dict[str, Any],
    resultado_parser: Dict[str, Any],
    tempo_total: float,
) -> None:
    """Saída formatada usando Rich (quando disponível)."""
    console = Console()

    console.print(
        Panel.fit(
            "[bold green]✓ Extração concluída[/bold green]",
            title="SOG — Extrator PDF",
            border_style="green",
        )
    )

    tabela = Table(title="Resumo Executivo", show_header=True, header_style="bold cyan")
    tabela.add_column("Campo", style="dim")
    tabela.add_column("Valor")

    tabela.add_row("Sucumbente", resultado_sentenca.get("sucumbente_nome", "—") or "—")
    tabela.add_row("Tipo", resultado_sentenca.get("sucumbente_tipo", "—") or "—")
    tabela.add_row("Valor Condenação", resultado_sentenca.get("valor_condenacao", "—") or "—")
    tabela.add_row("Honorários %", resultado_sentenca.get("honorarios_percentual", "—") or "—")
    tabela.add_row(
        "Suspensão (art. 98 §3º)",
        "Sim" if resultado_sentenca.get("suspensao_exigibilidade") else "Não",
    )
    tabela.add_row("Método", resultado_sentenca.get("_metodo", "—"))
    tabela.add_row("Score", f"{resultado_sentenca.get('_score', 0):.2f}")
    tabela.add_row("Páginas", str(resultado_pdf.get("num_paginas", 0)))

    custas = resultado_pdf.get("custas_iniciais", {})
    if custas.get("encontrado"):
        tabela.add_row("Custas Iniciais", f"R$ {custas.get('valor_total', '—')}")
    else:
        tabela.add_row("Custas Iniciais", "Não encontradas")

    tabela.add_row("Tempo", f"{tempo_total:.2f}s")

    console.print(tabela)
    console.print("\n[bold]JSON — Resultado da sentença[/bold]")
    console.print(JSON.from_data(resultado_sentenca))
    console.print("\n[bold]JSON — Custas Iniciais[/bold]")
    console.print(JSON.from_data(custas))
    console.print("\n[bold]JSON — Resultado do parser[/bold]")
    console.print(JSON.from_data(resultado_parser))

    documentos_capa = resultado_pdf.get("documentos_capa", [])
    if documentos_capa:
        console.print(f"\n[bold]Documentos da capa ({len(documentos_capa)} encontrados)[/bold]")
        tabela_docs = Table(show_header=True, header_style="bold cyan")
        tabela_docs.add_column("Id.", style="dim", no_wrap=True)
        tabela_docs.add_column("Data")
        tabela_docs.add_column("Tipo")
        tabela_docs.add_column("Nome")
        for doc in documentos_capa[:50]:
            tabela_docs.add_row(
                doc.get("doc_id", "—"),
                doc.get("data_assinatura", "—"),
                doc.get("tipo", "—") or "—",
                doc.get("nome", "—") or "—",
            )
        if len(documentos_capa) > 50:
            tabela_docs.add_row("...", "...", f"+{len(documentos_capa) - 50} docs", "")
        console.print(tabela_docs)


def _montar_saida_ansi(
    resultado_pdf: Dict[str, Any],
    resultado_sentenca: Dict[str, Any],
    resultado_parser: Dict[str, Any],
    tempo_total: float,
) -> None:
    """Saída formatada usando códigos ANSI (fallback sem rich)."""
    print(f"{_ANSI_GREEN}{'=' * 60}{_ANSI_RESET}")
    print(f"{_ANSI_BOLD}SOG — Extrator PDF{_ANSI_RESET}")
    print(f"{_ANSI_GREEN}{'=' * 60}{_ANSI_RESET}")

    print(f"{_ANSI_CYAN}Sucumbente{_ANSI_RESET} : {resultado_sentenca.get('sucumbente_nome', '—') or '—'}")
    print(f"{_ANSI_CYAN}Tipo{_ANSI_RESET}       : {resultado_sentenca.get('sucumbente_tipo', '—') or '—'}")
    print(f"{_ANSI_CYAN}Valor{_ANSI_RESET}      : {resultado_sentenca.get('valor_condenacao', '—') or '—'}")
    print(
        f"{_ANSI_CYAN}Honorários{_ANSI_RESET} : {resultado_sentenca.get('honorarios_percentual', '—') or '—'}%"
    )
    print(
        f"{_ANSI_CYAN}Suspensão{_ANSI_RESET}  : {'Sim' if resultado_sentenca.get('suspensao_exigibilidade') else 'Não'}"
    )
    print(f"{_ANSI_CYAN}Método{_ANSI_RESET}     : {resultado_sentenca.get('_metodo', '—')}")
    print(f"{_ANSI_CYAN}Score{_ANSI_RESET}      : {resultado_sentenca.get('_score', 0):.2f}")
    print(f"{_ANSI_CYAN}Páginas{_ANSI_RESET}    : {resultado_pdf.get('num_paginas', 0)}")

    custas = resultado_pdf.get("custas_iniciais", {})
    if custas.get("encontrado"):
        print(f"{_ANSI_CYAN}Custas Iniciais{_ANSI_RESET} : R$ {custas.get('valor_total', '—')}")
    else:
        print(f"{_ANSI_CYAN}Custas Iniciais{_ANSI_RESET} : Não encontradas")

    print(f"{_ANSI_CYAN}Tempo{_ANSI_RESET}      : {tempo_total:.2f}s")
    print(f"{_ANSI_GREEN}{'=' * 60}{_ANSI_RESET}")

    print(f"\n{_ANSI_BOLD}--- JSON Sentença ---{_ANSI_RESET}")
    print(json.dumps(resultado_sentenca, indent=2, ensure_ascii=False))
    print(f"\n{_ANSI_BOLD}--- JSON Custas Iniciais ---{_ANSI_RESET}")
    print(json.dumps(custas, indent=2, ensure_ascii=False))
    print(f"\n{_ANSI_BOLD}--- JSON Parser ---{_ANSI_RESET}")
    print(json.dumps(resultado_parser, indent=2, ensure_ascii=False))

    documentos_capa = resultado_pdf.get("documentos_capa", [])
    if documentos_capa:
        print(f"\n{_ANSI_BOLD}--- Documentos da capa ({len(documentos_capa)} encontrados) ---{_ANSI_RESET}")
        for doc in documentos_capa[:50]:
            doc_id = doc.get("doc_id", "—")
            data = doc.get("data_assinatura", "—")
            tipo = doc.get("tipo", "—") or "—"
            nome = doc.get("nome", "—") or "—"
            print(f"  {_ANSI_CYAN}{doc_id}{_ANSI_RESET} | {data} | {tipo} | {nome[:60]}")
        if len(documentos_capa) > 50:
            print(f"  ... +{len(documentos_capa) - 50} documentos")



def _montar_saida(
    resultado_pdf: Dict[str, Any],
    resultado_sentenca: Dict[str, Any],
    resultado_parser: Dict[str, Any],
    tempo_total: float,
) -> None:
    """Delega para rich (se disponível) ou ANSI fallback."""
    if _RICH_DISPONIVEL:
        _montar_saida_colorida_rich(
            resultado_pdf, resultado_sentenca, resultado_parser, tempo_total
        )
    else:
        _montar_saida_ansi(
            resultado_pdf, resultado_sentenca, resultado_parser, tempo_total
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrai dados de sentença a partir de um PDF judicial."
    )
    parser.add_argument("caminho_pdf", help="Caminho para o arquivo PDF")
    parser.add_argument(
        "--verbose", action="store_true", help="Mostra o texto bruto extraído do PDF"
    )
    parser.add_argument(
        "--llm", action="store_true", help="Força uso do LLM no extrator de sentença"
    )
    parser.add_argument(
        "--area",
        choices=["civel", "trabalhista"],
        default="civel",
        help="Área do direito (default: civel)",
    )
    args = parser.parse_args()

    inicio = time.perf_counter()

    try:
        # 1. Extrair texto do PDF
        resultado_pdf = extrair_texto_pdf(args.caminho_pdf)
    except Exception as exc:
        _print_colorido(f"[ERRO] Falha ao extrair texto do PDF: {exc}", _ANSI_RED)
        return 1

    if resultado_pdf["erro"]:
        _print_colorido(f"[ERRO] {resultado_pdf['erro']}", _ANSI_RED)
        return 1

    if args.verbose:
        print("--- TEXTO BRUTO EXTRAÍDO ---")
        print(resultado_pdf["texto_completo"][:4000])
        print("--- FIM DO TEXTO BRUTO ---\n")

    if resultado_pdf["scanned"]:
        _print_colorido(
            "[AVISO] PDF detectado como scanned (sem texto selecionável).\n"
            "        OCR não está implementado. Encerrando.",
            _ANSI_RED,
        )
        return 2

    try:
        # 2. Extrair sentença do dispositivo
        texto_para_extracao = resultado_pdf["dispositivo"] or resultado_pdf["texto_completo"]
        resultado_sentenca = extrair_sentenca(
            texto_para_extracao,
            area=args.area,
            forcar_llm=args.llm,
        )

        # 3. Processar documentos (sentença + documentos da capa relevantes)
        TIPOS_RELEVANTES = {
            "Mandado",
            "Ofício",
            "Alvará",
            "Traslado",
            "Carta de Sentença",
            "AR",
            "AR/MP",
            "Diligência",
            "Comprovante de Pagamento de Custas",
            "Sentença",
            "Decisão",
        }
        _tipos_lower = {t.lower() for t in TIPOS_RELEVANTES}

        doc_sentenca = {
            "doc_id": "pdf_sentenca",
            "tipo": "Sentença",
            "nome": "Sentença",
            "data_assinatura": "",
        }

        documentos_capa = resultado_pdf.get("documentos_capa", [])
        docs_filtrados = [
            {
                "doc_id": doc["doc_id"],
                "tipo": doc["tipo"],
                "nome": doc["nome"],
                "data_assinatura": doc.get("data_assinatura", ""),
            }
            for doc in documentos_capa
            if doc.get("tipo", "").lower() in _tipos_lower
        ]

        docs_para_parser = [doc_sentenca] + docs_filtrados
        textos_para_parser = {doc["doc_id"]: "" for doc in docs_para_parser}
        textos_para_parser["pdf_sentenca"] = (
            resultado_pdf["dispositivo"] or resultado_pdf["texto_completo"]
        )
        resultado_parser = processar_documentos(docs_para_parser, textos_para_parser)

    except Exception as exc:
        _print_colorido(f"[ERRO] Falha ao processar sentença/parser: {exc}", _ANSI_RED)
        return 1

    fim = time.perf_counter()
    tempo_total = fim - inicio

    # 4. Imprimir resultado formatado
    _montar_saida(resultado_pdf, resultado_sentenca, resultado_parser, tempo_total)

    return 0


if __name__ == "__main__":
    sys.exit(main())
