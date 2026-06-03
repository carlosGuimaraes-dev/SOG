"""
Testes da captura de sessão a partir do Google Chrome monitorável por CDP.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from modulos.chrome_login_capture import capturar_sessoes_chrome


class FakeSyncPlaywright:
    def __init__(self, browser=None, error=None):
        self.browser = browser
        self.error = error

    def __enter__(self):
        chromium = MagicMock()
        if self.error:
            chromium.connect_over_cdp.side_effect = self.error
        else:
            chromium.connect_over_cdp.return_value = self.browser
        return MagicMock(chromium=chromium)

    def __exit__(self, exc_type, exc, traceback):
        return False


def fake_page(url, logged=False):
    page = MagicMock()
    page.url = url
    page.logged = logged
    return page


def fake_browser(*pages):
    context = MagicMock()
    context.pages = list(pages)
    for page in pages:
        page.context = context
    return MagicMock(contexts=[context])


def test_captura_aguarda_quando_chrome_cdp_indisponivel(tmp_path):
    with patch(
        "modulos.chrome_login_capture.sync_playwright",
        return_value=FakeSyncPlaywright(error=RuntimeError("ECONNREFUSED")),
    ):
        resultado = capturar_sessoes_chrome(
            lambda page: True,
            lambda page: True,
            tmp_path / "pje.json",
            tmp_path / "sistj.json",
        )

    assert resultado["ok"] is False
    assert resultado["reason"] == "chrome_indisponivel"


def test_captura_aguarda_quando_aba_esta_ausente(tmp_path):
    browser = fake_browser(fake_page("https://pje.tjdft.jus.br/pje", logged=True))

    with patch("modulos.chrome_login_capture.sync_playwright", return_value=FakeSyncPlaywright(browser)):
        resultado = capturar_sessoes_chrome(
            lambda page: page.logged,
            lambda page: page.logged,
            tmp_path / "pje.json",
            tmp_path / "sistj.json",
        )

    assert resultado["ok"] is False
    assert resultado["reason"] == "abas_ausentes"
    assert resultado["missing"] == ["sistjweb"]


def test_captura_aguarda_quando_algum_sistema_nao_esta_logado(tmp_path):
    browser = fake_browser(
        fake_page("https://pje.tjdft.jus.br/pje", logged=True),
        fake_page("https://sso.tjdft.jus.br/auth/realms/SUDES", logged=False),
    )

    with patch("modulos.chrome_login_capture.sync_playwright", return_value=FakeSyncPlaywright(browser)):
        resultado = capturar_sessoes_chrome(
            lambda page: page.logged,
            lambda page: page.logged,
            tmp_path / "pje.json",
            tmp_path / "sistj.json",
        )

    assert resultado["ok"] is False
    assert resultado["reason"] == "login_pendente"
    assert resultado["pending"] == ["sistjweb"]


def test_captura_grava_storage_dos_dois_sistemas_quando_logados(tmp_path):
    browser = fake_browser(
        fake_page("https://pje.tjdft.jus.br/pje/Painel/painel_usuario.seam", logged=True),
        fake_page("https://sistj.tjdft.jus.br/sistj/sistj", logged=True),
    )
    pje_storage = tmp_path / "auth" / "pje_storage.json"
    sistj_storage = tmp_path / "auth" / "sistj_storage.json"

    with patch("modulos.chrome_login_capture.sync_playwright", return_value=FakeSyncPlaywright(browser)):
        resultado = capturar_sessoes_chrome(
            lambda page: page.logged,
            lambda page: page.logged,
            pje_storage,
            sistj_storage,
        )

    assert resultado["ok"] is True
    context = browser.contexts[0]
    context.storage_state.assert_any_call(path=str(pje_storage))
    context.storage_state.assert_any_call(path=str(sistj_storage))
    assert Path(pje_storage).parent.exists()
