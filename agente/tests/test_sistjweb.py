from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modulos.sistjweb import SistjClient


class _FakePage:
    def __init__(self):
        self.load_states = []

    def wait_for_load_state(self, state):
        self.load_states.append(state)


class _FakeLocator:
    def __init__(self, count=0):
        self._count = count

    def count(self):
        return self._count


class _FakeLoginPage:
    def __init__(self, url: str, selectors=None):
        self.url = url
        self._selectors = selectors or {}

    def locator(self, selector: str):
        return _FakeLocator(self._selectors.get(selector, 0))


def test_preencher_retorna_etapas_ordenadas_e_dados_de_saida(monkeypatch):
    cliente = SistjClient()
    cliente._auth.page = _FakePage()

    monkeypatch.setattr(cliente, "_abrir_fluxo_preenchimento", lambda: "fluxo aberto")
    monkeypatch.setattr(
        cliente,
        "_preencher_dados_processo",
        lambda dados: {
            "valor_causa_atualizado": "999,99",
            "detalhe": "consulta concluida",
        },
    )
    monkeypatch.setattr(cliente, "_preencher_secao_custas", lambda dados: "1 sucumbente")
    monkeypatch.setattr(cliente, "_preencher_pecas_processuais", lambda dados: "sem pecas")

    def _outros_itens(dados, valor_causa_atualizado):
        assert valor_causa_atualizado == "999,99"
        return "1 item"

    monkeypatch.setattr(cliente, "_preencher_outros_itens", _outros_itens)
    monkeypatch.setattr(cliente, "_preencher_custas_pagas", lambda dados: "0 itens")
    monkeypatch.setattr(
        cliente,
        "_salvar_planilha",
        lambda numero: {
            "screenshot_path": f"/tmp/{numero}.png",
            "valor_total_recolher": "123,45",
            "detalhe": "valor total 123,45",
        },
    )

    resultado = cliente.preencher({}, "0000001-00.2024.8.07.0001")

    assert resultado["screenshot_path"] == "/tmp/0000001-00.2024.8.07.0001.png"
    assert resultado["valor_total_recolher"] == "123,45"
    assert [etapa["codigo"] for etapa in resultado["etapas"]] == [
        "navegacao",
        "dados_processo",
        "custas",
        "pecas_processuais",
        "outros_itens",
        "custas_pagas",
        "salvar",
    ]


def test_preencher_indica_etapa_que_falhou(monkeypatch):
    cliente = SistjClient()
    cliente._auth.page = _FakePage()

    monkeypatch.setattr(cliente, "_abrir_fluxo_preenchimento", lambda: "fluxo aberto")
    monkeypatch.setattr(
        cliente,
        "_preencher_dados_processo",
        lambda dados: {
            "valor_causa_atualizado": "999,99",
            "detalhe": "consulta concluida",
        },
    )
    monkeypatch.setattr(cliente, "_preencher_secao_custas", lambda dados: "1 sucumbente")
    monkeypatch.setattr(cliente, "_preencher_pecas_processuais", lambda dados: "sem pecas")
    monkeypatch.setattr(
        cliente,
        "_preencher_outros_itens",
        lambda dados, valor_causa_atualizado: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="outros_itens"):
        cliente.preencher({}, "0000001-00.2024.8.07.0001")


@pytest.mark.parametrize(
    "url",
    [
        "https://sso.tjdft.jus.br/auth/realms/tjdft/protocol/openid-connect/auth",
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    ],
)
def test_esta_logado_trata_urls_sso_como_login_pendente(url):
    cliente = SistjClient()
    page = _FakeLoginPage(url)

    assert cliente._esta_logado(page) is False


@pytest.mark.parametrize(
    "url",
    [
        "https://pje.tjdft.jus.br/pje/Processo/Consulta/listView.seam",
        "https://example.com/qualquer-coisa",
    ],
)
def test_esta_logado_rejeita_aba_que_nao_e_do_sistjweb(url):
    cliente = SistjClient()
    page = _FakeLoginPage(url)

    assert cliente._esta_logado(page) is False


def test_esta_logado_nao_considera_sessao_valida_sem_indicador_da_area_logada():
    cliente = SistjClient()
    page = _FakeLoginPage("https://sistj.tjdft.jus.br/sistj/sistj")

    assert cliente._esta_logado(page) is False
