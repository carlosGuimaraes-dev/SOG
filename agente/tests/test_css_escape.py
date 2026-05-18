"""Testes unitários para modulos.css_escape."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from modulos.css_escape import escape_for_css


def test_string_vazia():
    assert escape_for_css("") == ""


def test_aspas_simples():
    assert escape_for_css("D'AVILA") == "D\\'AVILA"


def test_aspas_duplas():
    assert escape_for_css('D"AVILA') == 'D\\"AVILA'


def test_backslash():
    assert escape_for_css("foo\\bar") == "foo\\\\bar"


def test_string_comum():
    assert escape_for_css("MARIA SILVA") == "MARIA SILVA"


def test_multiplos_caracteres_especiais():
    # Backslash + aspas simples + aspas duplas
    assert escape_for_css("\\'\"") == "\\\\\\'\\\""
