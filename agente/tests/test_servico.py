"""
Testes do loop de processamento de tarefas do serviço longo.
"""
import threading
from unittest.mock import MagicMock, patch

from modulos.auth_manager import ReautenticacaoNecessariaError
from servico import AgenteServico


def _servico_fake() -> AgenteServico:
    servico = AgenteServico.__new__(AgenteServico)
    servico._locks = {"pje": False, "sistj": False}
    servico.pje = MagicMock()
    servico.sistj = MagicMock()
    servico._set_status = MagicMock()
    servico._pausar_ciclo = MagicMock()
    servico._stop_event = threading.Event()
    servico._ler_comando = MagicMock(return_value=("iniciar", "executando"))
    return servico


def test_processa_cinco_tarefas_sequencialmente_sem_deadlock():
    servico = _servico_fake()
    tarefas = [
        {"id": idx, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}
        for idx in range(1, 6)
    ]

    with patch("servico.proxima_tarefa_pendente", side_effect=tarefas + [None]), \
         patch("servico.executar_tarefa", return_value={"ok": True}) as executar_mock, \
         patch("servico.concluir_tarefa", return_value=True) as concluir_mock, \
         patch("servico.devolver_tarefa_pendente") as devolver_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=5)

    assert processadas == 5
    assert executar_mock.call_count == 5
    assert concluir_mock.call_count == 5
    assert devolver_mock.call_count == 0
    assert servico._locks == {"pje": False, "sistj": False}


def test_cancelamento_durante_execucao_nao_prende_lock():
    servico = _servico_fake()
    tarefa = {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}

    with patch("servico.proxima_tarefa_pendente", side_effect=[tarefa, None]), \
         patch("servico.executar_tarefa", return_value={"ok": True}), \
         patch("servico.concluir_tarefa", return_value=False) as concluir_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=1)

    assert processadas == 1
    concluir_mock.assert_called_once_with(1, "concluido", resultado={"ok": True})
    assert servico._locks == {"pje": False, "sistj": False}


def test_comando_parar_interrompe_antes_da_proxima_tarefa_segura():
    servico = _servico_fake()
    servico._ler_comando = MagicMock(
        side_effect=[("iniciar", "executando"), ("parar", "executando")]
    )
    tarefas = [
        {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}},
        {"id": 2, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}},
    ]

    with patch("servico.proxima_tarefa_pendente", side_effect=tarefas), \
         patch("servico.executar_tarefa", return_value={"ok": True}) as executar_mock, \
         patch("servico.concluir_tarefa", return_value=True):
        processadas = servico._processar_tarefas_pendentes(max_tarefas=2)

    assert processadas == 1
    assert executar_mock.call_count == 1
    assert servico._locks == {"pje": False, "sistj": False}


def test_expiracao_sessao_devolve_tarefa_e_pausa_para_relogin():
    servico = _servico_fake()
    tarefa = {"id": 1, "tipo": "dummy", "sistema_alvo": "pje", "payload": {}}

    with patch("servico.proxima_tarefa_pendente", return_value=tarefa), \
         patch("servico.executar_tarefa", side_effect=ReautenticacaoNecessariaError("pje")), \
         patch("servico.concluir_tarefa") as concluir_mock, \
         patch("servico.devolver_tarefa_pendente") as devolver_mock:
        processadas = servico._processar_tarefas_pendentes(max_tarefas=1)

    assert processadas == 1
    devolver_mock.assert_called_once_with(1)
    concluir_mock.assert_not_called()
    servico._pausar_ciclo.assert_called_once_with(
        "aguardando_login",
        "Sessão pje expirada durante tarefa.",
    )
    assert servico._locks == {"pje": False, "sistj": False}
