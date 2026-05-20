"""
Testes do loop de processamento de tarefas do serviço longo.
"""
from unittest.mock import MagicMock, patch

from servico import AgenteServico


def _servico_fake() -> AgenteServico:
    servico = AgenteServico.__new__(AgenteServico)
    servico._locks = {"pje": False, "sistj": False}
    servico.pje = MagicMock()
    servico.sistj = MagicMock()
    servico._set_status = MagicMock()
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
