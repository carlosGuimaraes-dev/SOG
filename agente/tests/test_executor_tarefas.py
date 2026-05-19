"""
Testes do executor de tarefas do agente.
"""
import pytest
from unittest.mock import MagicMock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modulos.executor_tarefas import registrar, executar_tarefa, tipos_suportados


class TestRegistry:
    def test_registrar_handler(self):
        @registrar("teste_dummy")
        def handler_dummy(payload, pje, sistj):
            return {"ok": True, "payload": payload}

        assert "teste_dummy" in tipos_suportados()

    def test_tipos_suportados_inclui_handlers_principais(self):
        assert "verificar_sessao_pje" in tipos_suportados()
        assert "consultar_etiqueta_pje" in tipos_suportados()
        assert "preencher_sistj" in tipos_suportados()
        assert "anexar_demonstrativo_pje" in tipos_suportados()


class TestExecutarTarefa:
    def test_executar_tarefa_dummy(self):
        pje_mock = MagicMock()
        sistj_mock = MagicMock()

        @registrar("meu_teste")
        def _handler(payload, pje, sistj):
            return {"recebido": payload.get("x", 0)}

        tarefa = {"tipo": "meu_teste", "payload": {"x": 42}}
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["recebido"] == 42

    def test_executar_tarefa_desconhecida(self):
        pje_mock = MagicMock()
        sistj_mock = MagicMock()

        tarefa = {"tipo": "nao_existe", "payload": {}}
        with pytest.raises(ValueError, match="Tipo de tarefa desconhecido"):
            executar_tarefa(tarefa, pje_mock, sistj_mock)

    def test_executar_tarefa_payload_none(self):
        pje_mock = MagicMock()
        sistj_mock = MagicMock()

        @registrar("teste_payload_none")
        def _handler(payload, pje, sistj):
            return {"payload_is_dict": isinstance(payload, dict)}

        tarefa = {"tipo": "teste_payload_none"}  # sem payload
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["payload_is_dict"] is True

    def test_executar_verificar_sessao_pje(self):
        """Testa o handler placeholder de verificar_sessao_pje."""
        pje_mock = MagicMock()
        pje_mock._esta_logado.return_value = True
        pje_mock.page.url = "https://pje.tjdft.jus.br/"
        sistj_mock = MagicMock()

        tarefa = {"tipo": "verificar_sessao_pje", "payload": {}}
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["logado"] is True
        assert resultado["url_atual"] == "https://pje.tjdft.jus.br/"
        pje_mock._esta_logado.assert_called_once_with(pje_mock.page)

    def test_executar_verificar_sessao_pje_erro(self):
        """Testa que o handler placeholder trata exceção graciosamente."""
        pje_mock = MagicMock()
        pje_mock._esta_logado.side_effect = Exception("browser fechado")
        sistj_mock = MagicMock()

        tarefa = {"tipo": "verificar_sessao_pje", "payload": {}}
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["logado"] is False
        assert resultado["url_atual"] is None

    def test_executar_consultar_etiqueta_pje(self):
        pje_mock = MagicMock()
        pje_mock.coletar_lista_processos.return_value = ["0000001-01.2024.8.07.0001"]
        sistj_mock = MagicMock()

        tarefa = {"tipo": "consultar_etiqueta_pje", "payload": {}}
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["total"] == 1
        assert resultado["processos"] == ["0000001-01.2024.8.07.0001"]
        pje_mock.garantir_autenticado.assert_called_once()

    def test_executar_verificar_sessao_sistj(self):
        pje_mock = MagicMock()
        sistj_mock = MagicMock()
        sistj_mock._esta_logado.return_value = True
        sistj_mock.page.url = "https://sistj.tjdft.jus.br/"

        tarefa = {"tipo": "verificar_sessao_sistj", "payload": {}}
        resultado = executar_tarefa(tarefa, pje_mock, sistj_mock)

        assert resultado["logado"] is True
        assert resultado["url_atual"] == "https://sistj.tjdft.jus.br/"
        sistj_mock._esta_logado.assert_called_once_with(sistj_mock.page)
