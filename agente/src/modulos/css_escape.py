"""
Utilitário para escaping de strings em seletores CSS.

O pseudo-seletor :has-text() do Playwright (e outros motores CSS) interpreta
aspas e backslash como delimitadores/escape. Textos dinâmicos (nomes de
partes, números de processo, etiquetas) podem conter caracteres que quebram
o seletor ou, em casos extremos, permitem injeção CSS.

Uso:
    from modulos.css_escape import escape_for_css
    seletor = f"td:has-text('{escape_for_css(nome_parte)}')"
"""


def escape_for_css(texto: str) -> str:
    """
    Escapa backslash, aspas simples e aspas duplas para uso seguro
    em seletores CSS (especialmente dentro de :has-text()).

    Ordem de substituição importa: backslash deve ser escapado primeiro,
    senão o backslash inserido pelas aspas seria duplicado.
    """
    return texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
