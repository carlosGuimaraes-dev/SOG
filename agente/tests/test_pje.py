from unittest.mock import MagicMock

from modulos.pje import PjeClient


class _LocatorList:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class _BodyLocator:
    def __init__(self, text):
        self._text = text

    def inner_text(self, timeout=None):
        return self._text


class _CountLocator:
    def __init__(self, count=0):
        self._count = count

    def count(self):
        return self._count

    @property
    def first(self):
        return self

    def inner_text(self, timeout=None):
        return ""


class _RowLocator:
    def __init__(self, texts):
        self._texts = texts

    def all_inner_texts(self):
        return list(self._texts)


class _FakeRow:
    def __init__(self, texts):
        self._texts = texts

    def locator(self, selector):
        assert selector == ".rich-table-cell, td"
        return _RowLocator(self._texts)


class _FakePage:
    def __init__(self, rows, body_text="texto stale"):
        self._rows = rows
        self._body_text = body_text

    def wait_for_load_state(self, state):
        assert state == "networkidle"

    def wait_for_timeout(self, timeout):
        assert timeout in (2000, 3000)

    def locator(self, selector):
        if selector == ".rich-table-row, table tbody tr, .documento-item":
            return _LocatorList(self._rows)
        if selector == "body":
            return _BodyLocator(self._body_text)
        return _CountLocator(0)

    def frame_locator(self, selector):
        raise AssertionError(f"frame_locator nao deveria ser chamado: {selector}")

    def go_back(self):
        raise AssertionError("go_back nao deveria ser chamado quando o clique falha")


def test_coletar_documentos_nao_registra_texto_quando_click_do_documento_falha(monkeypatch):
    cliente = PjeClient()
    cliente._auth.page = _FakePage(
        rows=[_FakeRow(["ID 123", "2024-01-01", "Sentenca publicada", "Sentença"])]
    )

    monkeypatch.setattr("modulos.pje._safe_click", lambda *args, **kwargs: True)
    monkeypatch.setattr("modulos.pje._safe_wait", lambda *args, **kwargs: True)
    monkeypatch.setattr("modulos.pje._clicar_por_texto_exato", lambda *args, **kwargs: False)

    docs, textos = cliente.coletar_documentos("0000001-01.2024.8.07.0001")

    assert docs == [
        {
            "doc_id": "123",
            "tipo": "Sentença",
            "data_assinatura": "2024-01-01",
            "nome": "Sentenca publicada",
        }
    ]
    assert textos == {}
