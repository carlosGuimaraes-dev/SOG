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
