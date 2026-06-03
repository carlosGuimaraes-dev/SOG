from unittest.mock import MagicMock

from modulos.pje import PjeClient
from modulos.sistjweb import SistjClient


def _page(url: str):
    page = MagicMock()
    page.url = url
    page.locator.return_value.count.return_value = 0
    page.get_by_text.return_value.count.return_value = 0
    return page


def test_pje_nao_considera_sso_como_logado():
    client = PjeClient.__new__(PjeClient)
    page = _page("https://sso.cloud.pje.jus.br/auth/realms/pje/protocol/openid-connect/auth")

    assert client._esta_logado(page) is False


def test_sistjweb_nao_considera_sso_tjdft_como_logado():
    client = SistjClient.__new__(SistjClient)
    page = _page("https://sso.tjdft.jus.br/auth/realms/SUDES/protocol/openid-connect/auth")

    assert client._esta_logado(page) is False


def test_sistjweb_nao_considera_microsoft_sso_como_logado():
    client = SistjClient.__new__(SistjClient)
    page = _page("https://login.microsoftonline.com/common/oauth2/v2.0/authorize")

    assert client._esta_logado(page) is False
